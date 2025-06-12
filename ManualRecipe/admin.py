from django.contrib import admin
from .models import ManualRecipe

@admin.register(ManualRecipe)
class ManualRecipeAdmin(admin.ModelAdmin):
    list_display = ('dish_name', 'user', 'dish_price', 'date_to_serve', 'created_at', 'updated_at')
    search_fields = ('dish_name', 'user__username', 'menu_type', 'tags')
    list_filter = ('date_to_serve', 'created_at')