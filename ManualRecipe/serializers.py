from rest_framework import serializers
from .models import ManualRecipe
from accounts.models import User,Profile

class ManualRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManualRecipe
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Define required fields explicitly
        required_fields = [
            'dish_name', 'menu_type', 'dish_description',
            'ingredients', 'directions'
        ]

        # Make all other fields optional
        for field_name in self.fields:
            if field_name not in required_fields and field_name not in self.Meta.read_only_fields:
                self.fields[field_name].required = False




class UserRecipeSummarySerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(source='profile.fullname')
    image = serializers.ImageField(source='profile.image')
    recipe_count = serializers.IntegerField()

    class Meta:
        model = User
        fields = ['id', 'fullname', 'image', 'recipe_count']