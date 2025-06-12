from django.db import models
from accounts.models import User
# Create your models here.


class AIGeneratedRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_recipes')
    recipe_type = models.CharField(max_length=20, choices=[('food', 'Food'), ('cocktail', 'Cocktail')])
    main_ingredients = models.TextField()
    serving_size = models.PositiveIntegerField()
    exclusion = models.TextField(blank=True)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    



class RecipeStep(models.Model):
    recipe = models.ForeignKey(AIGeneratedRecipe, on_delete=models.CASCADE, related_name='steps')
    step_number = models.PositiveIntegerField()
    instruction = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['step_number']

    def __str__(self):
        return f"Step {self.step_number} for {self.recipe.title}"