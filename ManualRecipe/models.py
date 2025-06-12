from django.db import models
from accounts.models import User

class ManualRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manual_recipes')
    dish_name = models.CharField(max_length=255)

    menu_type = models.CharField(max_length=255, help_text="Comma-separated menu types (e.g. breakfast, lunch, dinner)")
    tags = models.CharField(max_length=255, help_text="Comma-separated tags (e.g. vegan, spicy, gluten-free)")

    dish_price = models.DecimalField(max_digits=8, decimal_places=2)
    food_cost = models.DecimalField(max_digits=8, decimal_places=2)
    food_percent_markup = models.DecimalField(max_digits=5, decimal_places=2, help_text="e.g., 25.00 for 25% markup")

    date_to_serve = models.DateField()
    cooking_station = models.CharField(max_length=255)

    text_instructions = models.TextField()
    dish_description = models.TextField()

    ingredients = models.TextField(help_text="List of ingredients (comma or line separated)")
    directions = models.TextField(help_text="Step-by-step cooking directions")

    image = models.ImageField(upload_to='recipes/images/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.dish_name} by {self.user.username}"
