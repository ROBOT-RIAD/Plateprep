from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ManualRecipe.views import ManualRecipeViewSet
from AiRecipe.views import AIGeneratedRecipeViewSet,CreateProTipsAPIView, ProTipsListAPIView

router = DefaultRouter()
router.register('manual-recipes', ManualRecipeViewSet, basename='manual-recipe')
router.register('ai-recipes', AIGeneratedRecipeViewSet, basename='ai-recipes')


urlpatterns = [
    path('', include(router.urls)),
    path('generate-pro-tips/<int:recipe_id>/', CreateProTipsAPIView.as_view(), name='generate_pro_tips'),
    path('pro-tips/', ProTipsListAPIView.as_view(), name='list_pro_tips'),
]