from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ManualRecipe.views import ManualRecipeViewSet

router = DefaultRouter()
router.register('manual-recipes', ManualRecipeViewSet, basename='manual-recipe')

urlpatterns = [
    path('', include(router.urls)),
]