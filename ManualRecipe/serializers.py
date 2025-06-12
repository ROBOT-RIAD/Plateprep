from rest_framework import serializers
from .models import ManualRecipe

class ManualRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManualRecipe
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']
