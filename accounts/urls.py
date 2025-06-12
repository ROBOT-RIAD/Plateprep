from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import GoogleLoginView,LoginAPIView,RegisterApiView,CustomTokenRefreshView,SendOTPView,VerifyOTPView,ResetPasswordView,ProfileViewSet
from subscription.views import PublicPackageListView

router = DefaultRouter()
router.register('profile', ProfileViewSet, basename='profile')

urlpatterns = [
    path('register/', RegisterApiView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='token_obtain_pair'),
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('packages/', PublicPackageListView.as_view(), name='public-package-list'),
    path('', include(router.urls)),
]
