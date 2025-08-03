from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from .serializers import RegisterSerializer,CustomTokenObtainPairSerializer,GoogleLoginSerializer,SendOTPSerializer,VerifyOTPSerializer,ResetPasswordSerializer,ProfileSerializer,UserWithProfileSerializer,VerifyEmailSerializer
from rest_framework.permissions import AllowAny,IsAuthenticated
from .models import User,Profile,PasswordResetOTP,EmailVerificationOTP
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from .permissions import IsAdminRole
from django.db.models.functions import TruncDate
from django.db.models import Count,Min
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
from dateutil.relativedelta import relativedelta
from datetime import date
from rest_framework.pagination import PageNumberPagination


class RegisterApiView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    @swagger_auto_schema(tags=["Authentication"])

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "Sign‑up successful."
                           "Please verify to activate your account."
            },
            status=status.HTTP_201_CREATED
        )
    



class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=VerifyEmailSerializer, tags=['Authentication'])
    def post(self, request):
        s = VerifyEmailSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        user = s.validated_data['user']
        otp_rec = s.validated_data['otp_rec']

        if otp_rec.is_expired():
            return Response({"error": "OTP expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Update user and OTP
        user.is_active = True
        user.is_email_verified = True
        user.save()

        otp_rec.is_verified = True
        otp_rec.save()


        # ✅ Delete all old OTPs for the user (clean up)
        EmailVerificationOTP.objects.filter(user=user).exclude(pk=otp_rec.pk).delete()

        # ✅ Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        refresh['email'] = user.email
        refresh['role'] = user.role

        # ✅ Return success response with tokens
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "email": user.email,
                "role": user.role,
                "name": user.profile.fullname if hasattr(user, 'profile') else None
            }
        }, status=status.HTTP_200_OK)



class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={'email': openapi.Schema(type=openapi.TYPE_STRING)}
        ),
        tags=['Authentication']
    )
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if user.is_email_verified:
                return Response({"error": "Email is already verified."}, status=status.HTTP_400_BAD_REQUEST)

            # Invalidate previous unverified OTPs
            EmailVerificationOTP.objects.filter(user=user, is_verified=False).delete()

            # Create new OTP
            otp_rec = EmailVerificationOTP.objects.create(user=user)

            # Send e‑mail
            send_mail(
                subject='Your new verification code',
                message=f'Your new OTP is: {otp_rec.otp}',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
            )

            return Response({"message": "A new OTP has been sent."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)



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
        print(request.data)
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




class AdminUserPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'




class AdminAllUsersView(APIView):
    permission_classes = [IsAdminRole]

    @swagger_auto_schema(
        operation_description="Retrieve all users with their profile data (excluding the current admin and superusers).",
        tags=['admin']
    )
    def get(self, request):
        users = User.objects.select_related('profile')\
            .exclude(id=request.user.id)\
            .filter(is_superuser=False).order_by('-date_joined')

        # Pagination setup
        paginator = AdminUserPagination()
        paginated_users = paginator.paginate_queryset(users, request)

        serializer = UserWithProfileSerializer(paginated_users, many=True, context={'request': request})

        # Stats
        total_users = User.objects.filter(is_superuser=False).count()
        total_recipes = ManualRecipe.objects.count()
        total_revenue = Subscription.objects.aggregate(total=Sum('price'))['total'] or 0
        total_active_subscriptions = Subscription.objects.filter(is_active=True).count()

        response_data = {
            "users": serializer.data,
            "stats": {
                "total_users": total_users,
                "total_recipes": total_recipes,
                "total_revenue": float(total_revenue),
                "total_active_subscriptions": total_active_subscriptions
            }
        }

        return paginator.get_paginated_response(response_data)


# class AdminAllUsersView(APIView):
#     permission_classes = [IsAdminRole]

#     @swagger_auto_schema(
#         operation_description="Retrieve all users with their profile data (excluding the current admin and superusers).",
#         tags=['admin']
#     )
#     def get(self, request):
#         users = User.objects.select_related('profile')\
#             .exclude(id=request.user.id)\
#             .filter(is_superuser=False)
#         serializer = UserWithProfileSerializer(users, many=True,context={'request': request})

#         total_users = User.objects.filter(is_superuser=False).count()
#         total_recipes = ManualRecipe.objects.count()
#         total_revenue = Subscription.objects.aggregate(total=Sum('price'))['total'] or 0
#         total_active_subscriptions = Subscription.objects.filter(is_active=True).count()
#         data = {
#             "users": serializer.data,
#             "stats": {
#                 "total_users": total_users,
#                 "total_recipes": total_recipes,
#                 "total_revenue": float(total_revenue),
#                 "total_active_subscriptions": total_active_subscriptions
#             }
#         }
#         return Response(data)
    



class UserMonthlyStatsView(APIView):
    permission_classes = [IsAdminRole]

    @swagger_auto_schema(
        operation_description="Get monthly stats: new users joined and cumulative total per month.",
        tags=['admin']
    )
    def get(self, request):
        today = now().date()

        # Start from January of current year
        start_month = date(today.year, 1, 1)
        current_month = today.replace(day=1)

        # Step 1: Build all months from Jan to current month
        all_months = []
        month_cursor = start_month
        while month_cursor <= current_month:
            all_months.append(month_cursor)
            month_cursor += relativedelta(months=1)

        # Step 2: Query actual user counts
        raw_data = (
            User.objects
            .annotate(month=TruncMonth('date_joined'))
            .values('month')
            .annotate(new_users=Count('id'))
            .order_by('month')
        )
        raw_dict = {item['month'].date(): item['new_users'] for item in raw_data}

        # Step 3: Build chart data
        chart_data = []
        cumulative = 0
        for month in all_months:
            new_users = raw_dict.get(month, 0)
            cumulative += new_users
            formatted_month = DateFormat(month).format('M-Y')  # Jan-2025
            chart_data.append({
                'month': formatted_month,
                'new_users': new_users,
                'total_users': cumulative
            })

        return Response(chart_data)
    



