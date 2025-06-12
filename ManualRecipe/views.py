from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import ManualRecipe
from .serializers import ManualRecipeSerializer
from accounts.permissions import IsMemberRole
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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
            required=["dish_name", "menu_type", "tags", "dish_price", "food_cost", "food_percent_markup",
                      "date_to_serve", "cooking_station", "text_instructions", "dish_description",
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