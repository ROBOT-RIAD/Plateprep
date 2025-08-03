from django.db import models
from accounts.models import User
from ManualRecipe.models import ManualRecipe
# Create your models here.


class AIGeneratedRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_recipes')
    recipe_type = models.CharField(max_length=20, choices=[('food', 'Food'), ('cocktail', 'Cocktail')])
    main_ingredients = models.TextField()
    serving_size = models.PositiveIntegerField()
    exclusion = models.TextField(blank=True)
    cuisine = models.CharField(max_length=300, blank=True)
    image_url = models.URLField(max_length=1024)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipe_type} by {self.user.username}"
    


class ProTips(models.Model):
    manual_recipe = models.OneToOneField(ManualRecipe, on_delete=models.CASCADE, related_name='pro_tips')
    tips = models.TextField(help_text="AI-generated pro tips for the recipe")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pro tips for {self.manual_recipe.dish_name}"






    
