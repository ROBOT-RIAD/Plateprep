from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import openai
from drf_yasg.utils import swagger_auto_schema
from accounts.permissions import IsMemberRole
from .models import AIGeneratedRecipe,ProTips
from .serializers import AIGeneratedRecipeSerializer,ProTipsSerializer
from .utils import parse_ai_recipe_response
from ManualRecipe.models import ManualRecipe
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
import logging
import requests
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image
import tempfile
from django.conf import settings
from django.core.files.storage import default_storage
from urllib.parse import quote


openai.api_key = settings.OPENAI_API_KEY
logger = logging.getLogger(__name__)



class AIGeneratedRecipeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsMemberRole]

    @swagger_auto_schema(tags=['Ai'], request_body=AIGeneratedRecipeSerializer)
    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        user = request.user
        data = request.data

        if user.role == 'member':
            if not user.subscriptions.filter(is_active=True).exists():
                ai_recipe_count = AIGeneratedRecipe.objects.filter(user=user).count()
                if ai_recipe_count >= 6:
                    return Response(
                        {"error": "You must buy a subscription to create more than 6 AI-generated recipes."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        recipe_type = data.get('recipe_type')
        cuisine = data.get('cuisine')
        main_ingredients = data.get('main_ingredients')
        serving_size = data.get('serving_size')
        exclusion = data.get('exclusion', '')

        if not all([recipe_type, cuisine, main_ingredients, serving_size]):
            return Response({"error": "Missing required fields."}, status=400)

        prompt = (
            f"Generate a recipe for {recipe_type} with the following details:\n"
            f"Generate a food image for {recipe_type} with the following details:\n...do not provide any kind of text with the image when showing the output..skip the label part..."
            f"Cuisine: {cuisine}\n"
            f"Main Ingredients: {main_ingredients}\n"
            f"Serving Size: {serving_size}\n"
        )
        if exclusion:
            prompt += f"Exclude ingredients or items: {exclusion}\n"
        prompt += "\nPlease provide a recipe name, followed by '#### Ingredients:' and '#### Instructions:'"

        prompt += (
            "\nPlease provide a recipe in the following format:\n"
            "### Recipe Name: <Name>\n"
            "### Description: <A short paragraph describing the dish>\n"
            "#### Ingredients:\n<List of ingredients>\n"
            "#### Instructions:\n<Step-by-step instructions>"                   
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}],
                temperature=0.7,
            )
            ai_text = response['choices'][0]['message']['content']
            parsed = parse_ai_recipe_response(ai_text)
            logger.info(f"Generating image with prompt: {prompt}")

            # Request image from OpenAI API
            image_response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="512x512"
            )
            image_url = image_response['data'][0]['url']  # URL returned by OpenAI

            # Download the image
            img_data = requests.get(image_url).content
            image = Image.open(BytesIO(img_data))

            # Save the image to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                image.save(tmp_file, format='JPEG')
                tmp_file.seek(0)

                # Create a Django ContentFile from the temporary file and specify a name
                filename = f"recipes/images/{user.username}_{recipe_type}_{str(serving_size)}.jpg"
                content_file = ContentFile(tmp_file.read(), name=filename)  # Set the 'name' attribute here
                # Save the recipe with the image
                recipe = AIGeneratedRecipe.objects.create(
                    user=user,
                    recipe_type=recipe_type,
                    main_ingredients=main_ingredients,
                    serving_size=serving_size,
                    exclusion=exclusion,
                    cuisine=cuisine,
                    image=content_file 
                )
                recipe.image_url = recipe.image
                recipe.save()

                resdata = AIGeneratedRecipeSerializer(recipe,context={'request': request}).data
                resdata['image_url'] = resdata['image']

            return Response({
                "recipe": resdata,
                "parsed_result": parsed
            }, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)




class CreateProTipsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsMemberRole]

    @swagger_auto_schema(
        operation_description="Generate AI-based pro tips for a specific recipe",
        tags=["Protips"],
        responses={
            201: ProTipsSerializer,
            400: "Error generating pro tips"
        },
        request_body=None
    )
    def post(self, request, recipe_id):
        # Get the ManualRecipe object from the database using recipe_id
        manual_recipe = get_object_or_404(ManualRecipe, id=recipe_id)

        try:
            # Check if the manual recipe belongs to the current user
            if manual_recipe.user != request.user:
                return Response({'error': 'You do not have permission to generate pro tips for this recipe.'}, status=status.HTTP_403_FORBIDDEN)
            

            user = request.user
            has_subscription = user.subscriptions.filter(is_active=True).exists()

            if user.role == 'member' and not has_subscription:
                pro_tips_count = ProTips.objects.filter(manual_recipe=manual_recipe).count()
                if pro_tips_count >= 3:
                    return Response(
                        {"error": "You must buy a subscription to create more than 3 pro tips."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Collect all relevant information from the ManualRecipe object
            prompt = f"Provide pro tips for preparing the dish '{manual_recipe.dish_name}'.\n"
            prompt += f"Description: {manual_recipe.dish_description}\n"
            prompt += f"Ingredients: {manual_recipe.ingredients}\n"
            prompt += f"Directions: {manual_recipe.directions}\n"
            prompt += f"Menu Type: {manual_recipe.menu_type}\n"
            prompt += f"Tags: {manual_recipe.tags}\n"
            prompt += f"Price: {manual_recipe.dish_price}\n"
            prompt += f"Food Cost: {manual_recipe.food_cost}\n"
            prompt += f"Cooking Station: {manual_recipe.cooking_station}\n"
            prompt += f"Instructions: {manual_recipe.text_instructions}\n"
            prompt += f"Additional Information: {manual_recipe.food_percent_markup}% markup\n"
            prompt += f"Date to serve: {manual_recipe.date_to_serve}\n"

            # Call OpenAI API to generate pro tips using ChatCompletion (gpt-4 or gpt-3.5-turbo)
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )

            pro_tips = response['choices'][0]['message']['content'].strip()

            pro_tips_entry = ProTips.objects.create(manual_recipe=manual_recipe, tips=pro_tips)
            serializer = ProTipsSerializer(pro_tips_entry)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': f'Error generating pro tips: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)




class ProTipsListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsMemberRole]
    @swagger_auto_schema(
        operation_description="List all pro tips, ordered by creation date",
        tags=["Protips"],
        responses={
            200: ProTipsSerializer(many=True),
            400: "Error fetching pro tips"
        }
    )
    def get(self, request):
        # Fetch all ProTips objects ordered by created_at
        # pro_tips = ProTips.objects.filter(user=request.user).order_by('-created_at')
        pro_tips = ProTips.objects.filter(manual_recipe__user=request.user).order_by('-created_at')


        # Serialize the response
        serializer = ProTipsSerializer(pro_tips, many=True,context = {'request':request})
        return Response(serializer.data)
    


