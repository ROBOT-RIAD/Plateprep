from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from .models import ManualRecipe
from .serializers import ManualRecipeSerializer,UserRecipeSummarySerializer
from accounts.permissions import IsMemberRole
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from accounts.permissions import IsAdminRole
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.models import User
from django.db.models import Count
from .pagination import StandardResultsSetPagination
from rest_framework.pagination import PageNumberPagination

# Create your views here.


class ManualRecipeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for members to manage their manual recipes.
    Only allows authenticated users with 'member' role to access.
    """
    serializer_class = ManualRecipeSerializer
    permission_classes = [permissions.IsAuthenticated, IsMemberRole]

    def get_queryset(self):
        """Return only recipes that belong to the current user."""
        return ManualRecipe.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Attach current user to the recipe."""
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="List all manual recipes created by the logged-in member.",
        tags=["Manual Recipes"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new manual recipe (with optional image upload).",
        tags=["Manual Recipes"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["dish_name", "menu_type", "tags", "dish_description",
                      "ingredients", "directions"],
            properties={
                'dish_name': openapi.Schema(type=openapi.TYPE_STRING),
                'menu_type': openapi.Schema(type=openapi.TYPE_STRING),
                'tags': openapi.Schema(type=openapi.TYPE_STRING),
                'dish_price': openapi.Schema(type=openapi.TYPE_STRING, format='decimal'),
                'food_cost': openapi.Schema(type=openapi.TYPE_STRING, format='decimal'),
                'food_percent_markup': openapi.Schema(type=openapi.TYPE_STRING, format='decimal'),
                'date_to_serve': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'cooking_station': openapi.Schema(type=openapi.TYPE_STRING),
                'text_instructions': openapi.Schema(type=openapi.TYPE_STRING),
                'dish_description': openapi.Schema(type=openapi.TYPE_STRING),
                'ingredients': openapi.Schema(type=openapi.TYPE_STRING),
                'directions': openapi.Schema(type=openapi.TYPE_STRING),
                'image': openapi.Schema(type=openapi.TYPE_FILE),
            }
        )
    )
    def create(self, request, *args, **kwargs):
        print("CREATE payload:", request.data)
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a specific manual recipe owned by the logged-in member.",
        tags=["Manual Recipes"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a specific manual recipe.",
        tags=["Manual Recipes"]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a manual recipe.",
        tags=["Manual Recipes"]
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a manual recipe.",
        tags=["Manual Recipes"]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    


class StandardResultsSetPaginatio(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'


class AdminUserRecipeStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    pagination_class = StandardResultsSetPaginatio

    @swagger_auto_schema(
        operation_description="Retrieve paginated list of users who have created at least one recipe, including their profile info and recipe count.",
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Number of users per page",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={200: UserRecipeSummarySerializer(many=True)},
        tags=['admin']
    )
    def get(self, request):
        users_with_recipes = User.objects.annotate(recipe_count=Count('manual_recipes'))\
            .filter(recipe_count__gt=0)\
            .select_related('profile')

        # Manual pagination logic
        paginator = StandardResultsSetPaginatio()
        page = paginator.paginate_queryset(users_with_recipes, request)
        serializer = UserRecipeSummarySerializer(page, many=True,context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    




class AdminUserRecipeListView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="Retrieve all recipes created by a specific user using their user_id.",
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,
                description="ID of the user whose recipes are to be retrieved",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Results per page",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={200: ManualRecipeSerializer(many=True)},
        tags=["admin"]
    )
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "user_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        recipes = ManualRecipe.objects.filter(user=user).order_by('-created_at')
        serializer = ManualRecipeSerializer(recipes, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)