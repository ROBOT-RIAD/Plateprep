from rest_framework import serializers
from .models import AIGeneratedRecipe

class AIGeneratedRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIGeneratedRecipe
        fields = '__all__'
        read_only_fields = ['user']
