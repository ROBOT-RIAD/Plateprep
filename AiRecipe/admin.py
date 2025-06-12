from django.contrib import admin
from .models import AIGeneratedRecipe, RecipeStep

class RecipeStepInline(admin.TabularInline):
    model = RecipeStep
    extra = 1
    ordering = ['step_number']
    readonly_fields = ('created_at',)

@admin.register(AIGeneratedRecipe)
class AIGeneratedRecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'recipe_type', 'serving_size', 'created_at')
    list_filter = ('recipe_type', 'created_at')
    search_fields = ('title', 'main_ingredients', 'description')
    readonly_fields = ('created_at',)
    inlines = [RecipeStepInline]

@admin.register(RecipeStep)
class RecipeStepAdmin(admin.ModelAdmin):
    list_display = ('step_number', 'recipe', 'instruction', 'created_at')
    list_filter = ('recipe',)
    search_fields = ('instruction',)
    readonly_fields = ('created_at',)
