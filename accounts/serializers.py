from rest_framework import serializers
from .models import User,Profile,EmailVerificationOTP
from django.conf import settings
from django.core.mail import send_mail
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
        user = User.objects.create_user(
            username = validated_data['email'],
            email    = validated_data['email'],
            password = validated_data['password'],
            role     = validated_data['role'],
            is_active=False,                
        )
        Profile.objects.create(user=user)

        # 1️⃣ create OTP object
        otp_obj = EmailVerificationOTP.objects.create(user=user)

        # 2️⃣ e‑mail it
        send_mail(
            subject='Verify your account',
            message=f'Your verification code is {otp_obj.otp}',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        return user
    



class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp   = serializers.CharField(max_length=4)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email address.")

        try:
            otp_rec = EmailVerificationOTP.objects.filter(
                user=user, otp=attrs['otp'], is_verified=False
            ).latest('created_at')
        except EmailVerificationOTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP.")

        # 🔥 Check if OTP is expired here
        if otp_rec.is_expired():
            raise serializers.ValidationError("OTP has expired. Please request a new one.")

        attrs['user'] = user
        attrs['otp_rec'] = otp_rec
        return attrs
    



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[('chef', 'Chef'), ('member', 'Member'),('admin','Admin')], required=True)

    class Meta:
        model = User
        fields = ['email', 'password','role']

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        requested_role = attrs.get("role")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password")
        
        if user.role != requested_role:
            raise serializers.ValidationError("Role does not match the user's assigned role.")
        
        if not user.is_email_verified:
            raise serializers.ValidationError("Please verify your e‑mail before logging in.")

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
    


class ExtendedFileField(serializers.FileField):
    def to_representation(self, value):
        if value:
            request = self.context.get('request')
            url = getattr(value, 'url', value)
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None


class ProfileSerializer(serializers.ModelSerializer):
    image = ExtendedFileField(required=False)
    
    class Meta:
        model = Profile
        fields = [
            'id', 
            'fullname', 
            'phone_number', 
            'gender', 
            'date_of_birth', 
            'image',
            'bio',            
            'instagram',     
            'facebook',        
            'linkedin',     
            'twitter',        
            'address',        
            'website_link'
        ]





class UserWithProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['email', 'role', 'profile']