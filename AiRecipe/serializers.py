from rest_framework import serializers
from .models import AIGeneratedRecipe,ProTips
from ManualRecipe.serializers import ManualRecipeSerializer

class AIGeneratedRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIGeneratedRecipe
        fields = '__all__'
        read_only_fields = ['user']



class ProTipsSerializer(serializers.ModelSerializer):
    manual_recipe = ManualRecipeSerializer()
    class Meta:
        model = ProTips
        fields = ['manual_recipe', 'tips', 'created_at', 'updated_at']