from django.db import models
from accounts.models import User
# Create your models here.


class AIGeneratedRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_recipes')
    recipe_type = models.CharField(max_length=20, choices=[('food', 'Food'), ('cocktail', 'Cocktail')])
    main_ingredients = models.TextField()
    serving_size = models.PositiveIntegerField()
    exclusion = models.TextField(blank=True)
    cuisine = models.CharField(max_length=300, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipe_type} by {self.user.username}"



    
