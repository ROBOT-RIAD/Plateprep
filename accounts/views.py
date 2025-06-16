from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from .serializers import RegisterSerializer,CustomTokenObtainPairSerializer,GoogleLoginSerializer,SendOTPSerializer,VerifyOTPSerializer,ResetPasswordSerializer,ProfileSerializer,UserWithProfileSerializer
from rest_framework.permissions import AllowAny,IsAuthenticated
from .models import User,Profile,PasswordResetOTP
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from .permissions import IsAdminRole
from django.db.models.functions import TruncDate
from django.db.models import Count
from drf_yasg import openapi
from datetime import timedelta
from django.utils.timezone import now
from ManualRecipe.models import ManualRecipe
from subscription.models import Subscription
from django.db.models import Sum, Count

# Create your views here.
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.exceptions import ValidationError
from drf_yasg import openapi

# auth 
from firebase_admin import auth as firebase_auth
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models.functions import TruncMonth
from django.utils.dateformat import DateFormat



class RegisterApiView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    @swagger_auto_schema(tags=["Authentication"])

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'email': user.email,
                    'role': user.role,
                    'name': user.profile.fullname if hasattr(user, 'profile') else '',
                }
            }, status=status.HTTP_201_CREATED)

        except ValidationError as ve:
            return Response({"errors": ve.detail}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        request_body=GoogleLoginSerializer,
        tags=["Authentication"]
    )
    def post(self, request):
        id_token = request.data.get('idToken')  

        if not id_token:
            return Response({'error': 'Missing ID token'}, status=400)

        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            email = decoded_token.get('email')
            uid = decoded_token.get('uid')
            name = decoded_token.get('name')
            photo = decoded_token.get('picture')

            if not email:
                return Response({'error': 'Email not provided by Google'}, status=400)

            # Try to get existing user
            try:
                user = User.objects.get(email=email)
                created = False
            except User.DoesNotExist:
                created = True
                role = request.data.get('role')
                if role not in ['chef', 'member']:
                    return Response({'error': 'New users must provide a valid role (chef or member)'}, status=400)
                
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=User.objects.make_random_password(),
                    role=role
                )
                Profile.objects.create(
                    user=user,
                    fullname=name,
                    image=photo,
                )

            # Generate JWT token
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'email': user.email,
                    'role': user.role,
                    'name': user.profile.fullname,
                }
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        




class LoginAPIView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer
    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        try:
            return super().post(request,*args,**kwargs)
        except ValidationError as ve:
            return Response({"error": ve.detail}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e :
            return Response({"error": str(e)}, status= status.HTTP_500_INTERNAL_SERVER_ERROR)
    



class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e :
            return Response({"error":str(e)} , status= status.HTTP_500_INTERNAL_SERVER_ERROR)






class SendOTPView(APIView):
    permission_classes = [AllowAny]
 
    @swagger_auto_schema(
        request_body=SendOTPSerializer,
        tags=["Forgot Password"],
        operation_summary="Send OTP to email",
        responses={200: openapi.Response('OTP sent'), 400: 'Bad Request'}
    )
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            otp_record = PasswordResetOTP.objects.create(user=user)
            refresh = RefreshToken.for_user(user)
            refresh['email'] = user.email

            # print(otp_record.otp)
            print(email)


            # Send OTP via email
            send_mail(
            subject='Your OTP Code',
            message=f'Your OTP is: {otp_record.otp}',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            )

            return Response({
                "message": "OTP sent to your email.",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Failed to send OTP."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=VerifyOTPSerializer,
        tags=["Forgot Password"],
        operation_summary="Verify OTP",
        responses={200: openapi.Response('OTP verified'), 400: 'Invalid OTP'}
    )

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            otp_record = PasswordResetOTP.objects.filter(
                user=user, otp=otp, is_verified=False
            ).latest('created_at')
        except PasswordResetOTP.DoesNotExist:
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        otp_record.is_verified = True
        otp_record.save()

        return Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)



class ResetPasswordView(APIView):
    permission_classes = [AllowAny] 

    @swagger_auto_schema(
        request_body=ResetPasswordSerializer,
        manual_parameters=[
            openapi.Parameter(
                'email',
                openapi.IN_QUERY,
                description="Email address to reset password for",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        tags=["Forgot Password"],
        operation_summary="Reset password after OTP verification",
        responses={200: openapi.Response('Password reset successful'), 400: 'Bad Request'}
    )

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = request.query_params.get('email')
        if not email:
            return Response({"error": "Email is required in query params."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            otp_record = PasswordResetOTP.objects.filter(
                user=user, is_verified=True
            ).latest('created_at')
        except PasswordResetOTP.DoesNotExist:
            return Response({"error": "OTP not verified or expired."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            otp_record.delete()
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error" : e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class ProfileViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        return profile

    @swagger_auto_schema(responses={200: ProfileSerializer()})
    @action(detail=False, methods=['get'])
    def me(self, request):
        profile = self.get_object()
        serializer = ProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(request_body=ProfileSerializer, responses={200: ProfileSerializer()})
    @action(detail=False, methods=['patch'])
    def update_me(self, request):
        profile = self.get_object()
        serializer = ProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @swagger_auto_schema(responses={204: 'Profile deleted successfully'})
    @action(detail=False, methods=['delete'])
    def delete_me(self, request):
        profile = self.get_object()
        profile.delete()
        return Response({"detail": "Profile deleted successfully."}, status=status.HTTP_204_NO_CONTENT)







class AdminAllUsersView(APIView):
    permission_classes = [IsAdminRole]

    @swagger_auto_schema(
        operation_description="Retrieve all users with their profile data (excluding the current admin and superusers).",
        tags=['admin']
    )
    def get(self, request):
        users = User.objects.select_related('profile')\
            .exclude(id=request.user.id)\
            .filter(is_superuser=False)
        serializer = UserWithProfileSerializer(users, many=True,context={'request': request})

        total_users = User.objects.filter(is_superuser=False).count()
        total_recipes = ManualRecipe.objects.count()
        total_revenue = Subscription.objects.aggregate(total=Sum('price'))['total'] or 0
        total_active_subscriptions = Subscription.objects.filter(is_active=True).count()
        data = {
            "users": serializer.data,
            "stats": {
                "total_users": total_users,
                "total_recipes": total_recipes,
                "total_revenue": float(total_revenue),
                "total_active_subscriptions": total_active_subscriptions
            }
        }
        return Response(data)
    





class UserMonthlyStatsView(APIView):
    permission_classes = [IsAdminRole]

    @swagger_auto_schema(
        operation_description="Get monthly stats: new users joined and cumulative total per month.",
        tags=['admin']
    )
    def get(self, request):
        # Group users by month of date_joined
        raw_data = (
            User.objects
            .annotate(month=TruncMonth('date_joined'))
            .values('month')
            .annotate(new_users=Count('id'))
            .order_by('month')
        )

        # Build chart data with cumulative totals
        chart_data = []
        cumulative = 0

        for item in raw_data:
            month = item['month']
            new_users = item['new_users']
            cumulative += new_users
            formatted_month = DateFormat(month).format('M-Y')  # e.g., Jan-2025

            chart_data.append({
                'month': formatted_month,
                'new_users': new_users,
                'total_users': cumulative
            })

        return Response(chart_data)