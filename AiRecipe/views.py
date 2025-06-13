from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import openai
from drf_yasg.utils import swagger_auto_schema
from accounts.permissions import IsMemberRole

from .models import AIGeneratedRecipe
from .serializers import AIGeneratedRecipeSerializer
from .utils import parse_ai_recipe_response

openai.api_key = settings.OPENAI_API_KEY

class AIGeneratedRecipeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,IsMemberRole]

    @swagger_auto_schema(tags=['Ai'],request_body=AIGeneratedRecipeSerializer)
    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        user = request.user
        data = request.data

        recipe_type = data.get('recipe_type')
        cuisine = data.get('cuisine')
        main_ingredients = data.get('main_ingredients')
        serving_size = data.get('serving_size')
        exclusion = data.get('exclusion', '')

        if not all([recipe_type, cuisine, main_ingredients, serving_size]):
            return Response({"error": "Missing required fields."}, status=400)

        prompt = (
            f"Generate a recipe for {recipe_type} with the following details:\n"
            f"Cuisine: {cuisine}\n"
            f"Main Ingredients: {main_ingredients}\n"
            f"Serving Size: {serving_size}\n"
        )
        if exclusion:
            prompt += f"Exclude ingredients or items: {exclusion}\n"
        prompt += "\nPlease provide a recipe name, followed by '#### Ingredients:' and '#### Instructions:'"

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=700
            )
            ai_text = response['choices'][0]['message']['content']
            parsed = parse_ai_recipe_response(ai_text)

            recipe = AIGeneratedRecipe.objects.create(
                user=user,
                recipe_type=recipe_type,
                main_ingredients=main_ingredients,
                serving_size=serving_size,
                exclusion=exclusion,
                cuisine=cuisine
            )

            return Response({
                "recipe": AIGeneratedRecipeSerializer(recipe).data,
                "parsed_result": parsed
            }, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
