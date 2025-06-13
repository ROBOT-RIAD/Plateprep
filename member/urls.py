from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ManualRecipe.views import ManualRecipeViewSet
from AiRecipe.views import AIGeneratedRecipeViewSet

router = DefaultRouter()
router.register('manual-recipes', ManualRecipeViewSet, basename='manual-recipe')
router.register('ai-recipes', AIGeneratedRecipeViewSet, basename='ai-recipes')

urlpatterns = [
    path('', include(router.urls)),
]