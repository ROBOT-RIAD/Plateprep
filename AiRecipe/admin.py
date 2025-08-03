from django.contrib import admin
from .models import AIGeneratedRecipe,ProTips



@admin.register(AIGeneratedRecipe)
class AIGeneratedRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe_type', 'cuisine', 'serving_size', 'created_at')
    search_fields = ('user__username', 'cuisine', 'main_ingredients')
    list_filter = ('recipe_type', 'cuisine', 'created_at')
   

@admin.register(ProTips)
class ProTipsAdmin(admin.ModelAdmin):
    list_display = ('manual_recipe', 'tips', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    # Optionally, you can add a custom form layout
    fieldsets = (
        (None, {
            'fields': ('manual_recipe', 'tips')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )