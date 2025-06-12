from rest_framework import serializers
from .models import User,Profile

# jwt
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required= True)
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[('chef', 'Chef'), ('member', 'Member')], required=True)
    class Meta:
        model = User
        fields = ['email', 'password', 'role']
    
    def validate_role(self,value):
        allowed_role = ['chef','member']
        if value not in allowed_role:
            raise serializers.ValidationError("Only 'chef' and 'member' roles are allowed for registration.")
        return value
    

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        role = validated_data['role']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            role=role
        )
        Profile.objects.create(user=user)
        return user
    



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password']

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password")

        data = super().validate({'email': user.email, 'password': password})

        # Add user info to response
        data['user'] = {
            'email': user.email,
            'role': user.role,
            'name': user.profile.fullname if hasattr(user, 'profile') else '',
        }

        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        token['role'] = user.role
        return token



class GoogleLoginSerializer(serializers.Serializer):
    idToken = serializers.CharField()
    role = serializers.ChoiceField(choices=[('chef', 'chef'), ('member', 'member')], required=False)





class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)



class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=4)
    confirm_password = serializers.CharField(write_only=True, min_length=4)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs
    





class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'fullname', 'phone_number', 'gender', 'date_of_birth', 'image']






class UserWithProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['email', 'role', 'profile']