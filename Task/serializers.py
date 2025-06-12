from rest_framework import serializers
from .models import Task
from accounts.models import User


class TaskSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True, help_text="Email of the user to assign the task to")
    

    class Meta:
        model = Task
        fields = ['id', 'task_name', 'date', 'duration', 'email', 'status', 'assigned_by', 'assigned_to', 'created_at', 'updated_at']
        read_only_fields = ['assigned_by', 'assigned_to', 'created_at', 'updated_at']

    def create(self, validated_data):
        email = validated_data.pop('email')
        try:
            assigned_to_user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'User with this email does not exist.'})

        validated_data['assigned_by'] = self.context['request'].user
        validated_data['assigned_to'] = assigned_to_user
        return Task.objects.create(**validated_data)
    

