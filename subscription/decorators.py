from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from .models import Subscription



def subscription_required(view_func):
    """Decorator to check if the user has an active subscription, 
       but allow 'admin' users to bypass the check."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        # If the user is an admin, allow access without checking the subscription
        if user.role == 'admin':
            return view_func(request, *args, **kwargs)

        # Check if the user has the 'member' role and if they have an active subscription
        if user.role != 'member':
            return Response({"error": "You are not a valid user."}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Check if the user has an active subscription
            subscription = user.subscriptions.filter(is_active=True).latest('created_at')
            if subscription.is_active_subscription():  # Ensure that `is_active_subscription` is a method in your model
                return view_func(request, *args, **kwargs)
            else:
                return Response({"error": "You do not have an active subscription plan."}, status=status.HTTP_403_FORBIDDEN)
        except Subscription.DoesNotExist:
            return Response({"error": "You do not have an active subscription plan."}, status=status.HTTP_403_FORBIDDEN)

    return _wrapped_view