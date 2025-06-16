from rest_framework.routers import DefaultRouter
from subscription.views import PackageViewSet
from django.urls import path, include
from accounts.views import AdminAllUsersView, UserMonthlyStatsView
from ManualRecipe.views import AdminUserRecipeStatsView,AdminUserRecipeListView
from Task.views import AdminAllTasksListView

router = DefaultRouter()
router.register('packages', PackageViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('users/', AdminAllUsersView.as_view(), name='admin-all-users'),
    path('user-Monthly-stats/', UserMonthlyStatsView.as_view(), name='user-daily-stats'),
    path('users-with-recipes/', AdminUserRecipeStatsView.as_view(), name='admin-users-recipes'),
    path('user-recipes/', AdminUserRecipeListView.as_view(), name='admin-user-recipes'),
    path('tasks/', AdminAllTasksListView.as_view(), name='admin-task-list'),
]