from django.contrib import admin
from .models import AIGeneratedRecipe



@admin.register(AIGeneratedRecipe)
class AIGeneratedRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe_type', 'cuisine', 'serving_size', 'created_at')
    search_fields = ('user__username', 'cuisine', 'main_ingredients')
    list_filter = ('recipe_type', 'cuisine', 'created_at')
   


