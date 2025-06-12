from rest_framework.routers import DefaultRouter
from subscription.views import PackageViewSet
from django.urls import path, include

router = DefaultRouter()
router.register('packages', PackageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]