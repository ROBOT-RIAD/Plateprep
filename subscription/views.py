import stripe
from django.conf import settings
from rest_framework import viewsets,permissions,status,generics
from .models import Package,Subscription,StripeEventLog
from .serializers import PackageSerializer
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator
from accounts.permissions import IsAdminRole
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import IsMemberRole
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from accounts.models import User
from django.utils import timezone
from datetime import datetime
from pytz import timezone as dt_timezone
from drf_yasg import openapi
from datetime import datetime, timezone as dt_timezone


stripe.api_key = settings.STRIPE_SECRET_KEY




@method_decorator(name='list', decorator=swagger_auto_schema(tags=['Packages']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Packages']))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=['Packages']))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=['Packages']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=['Packages']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=['Packages']))
class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes=[permissions.IsAuthenticated , IsAdminRole]

    def perform_create(self, serializer):
        data = serializer.validated_data

        # Create Stripe Product
        stripe_product = stripe.Product.create(
            name=data['name'],
            description=data.get('description', ''),
            images=[]  # You can upload image URLs to Stripe if needed
        )

        # Create Stripe Price
        recurring_config = {
            "interval": data['billing_interval'],
            "interval_count": data.get('interval_count', 1)
        } if data['recurring'] else None

        price = stripe.Price.create(
            product=stripe_product.id,
            unit_amount=data['amount'],
            currency='usd',
            recurring=recurring_config if recurring_config else None
        )

        serializer.save(
            product_id=stripe_product.id,
            price_id=price.id
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        data = serializer.validated_data

        name = data.get('name', instance.name)
        description = data.get('description', instance.description)

        # Update Stripe Product name and description
        if instance.product_id:
            try:
                stripe.Product.modify(
                    instance.product_id,
                    name=name,
                    description=description
                )
            except Exception as e:
                print(f"Stripe update error: {e}")

        # If amount, interval, or recurrence changed => create a new price
        amount = data.get('amount', instance.amount)
        billing_interval = data.get('billing_interval', instance.billing_interval)
        interval_count = data.get('interval_count', instance.interval_count)
        recurring = data.get('recurring', instance.recurring)

        # If any price-related field changed, create a new Price
        if (
            amount != instance.amount or
            billing_interval != instance.billing_interval or
            interval_count != instance.interval_count or
            recurring != instance.recurring
        ):
            recurring_config = {
                "interval": billing_interval,
                "interval_count": interval_count
            } if recurring else None

            try:
                new_price = stripe.Price.create(
                    product=instance.product_id,
                    unit_amount=amount,
                    currency='usd',
                    recurring=recurring_config
                )
                # Save new price_id in DB
                serializer.save(price_id=new_price.id)
                return
            except Exception as e:
                print(f"Stripe price create error: {e}")

        # No price-related changes — just save updated fields
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.product_id:
            try:
                stripe.Product.modify(instance.product_id, active=False)
            except Exception as e:
                print(f"Stripe delete error: {e}")

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()




class PublicPackageListView(generics.ListAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [permissions.AllowAny]



###Subscriptions

class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated,IsMemberRole]

    @swagger_auto_schema(
        tags=["subscriptions"],
        operation_summary="Create Stripe Checkout Session",
        operation_description="Creates a Stripe Checkout Session for a subscription using the provided Stripe `price_id`.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['price_id'],
            properties={
                'price_id': openapi.Schema(type=openapi.TYPE_STRING, description="Stripe Price ID"),
            },
        ),
        responses={
            200: openapi.Response(
                description="Checkout session created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'url': openapi.Schema(type=openapi.TYPE_STRING, description='Stripe checkout URL'),
                    }
                )
            ),
            400: openapi.Response(description="Bad request or error"),
        }
    )

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            price_id = request.data.get("price_id")
            if not price_id:
                return Response({'error': 'price_id is required'}, status=400)
            

            active_subscription = Subscription.objects.filter(
            user=user,
            is_active=True,
            current_period_end__gt=timezone.now()
            ).first()

            if active_subscription:
                return Response({
                    'error': 'You already have an active subscription. Please cancel it before subscribing to a new package.'
                }, status=400)

            checkout_session = stripe.checkout.Session.create(
                customer_email=user.email,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url='http://127.0.0.1:8000/',
                cancel_url='http://127.0.0.1:8000/',
            )

            return Response({'url': checkout_session.url})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        





@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=["subscriptions"],)
    
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        # Step 1: Verify webhook
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except Exception as e:
            return JsonResponse({'error': f'Invalid signature: {str(e)}'}, status=400)

        event_id = event['id']
        event_type = event['type']
        data = event['data']['object']

        # Step 2: Prevent duplicate handling
        if StripeEventLog.objects.filter(event_id=event_id).exists():
            return HttpResponse(status=200)

        # Step 3: Log the event
        StripeEventLog.objects.create(
            event_id=event_id,
            event_type=event_type,
            payload=event
        )

        # Step 4: Handle event types
        try:
            with transaction.atomic():
                if event_type == 'checkout.session.completed':
                    session = data
                    customer_email = session.get('customer_email')
                    subscription_id = session.get('subscription')

                    user = User.objects.filter(email=customer_email).first()
                    if not user:
                        raise Exception("User not found.")

                    stripe_sub = stripe.Subscription.retrieve(subscription_id, expand=['items'])
                    item = stripe_sub['items']['data'][0] if stripe_sub['items']['data'] else None
                    price = item.get('price') if item else None

                    product_id = price.get('product') if price else None
                    product = stripe.Product.retrieve(product_id) if product_id else None
                    product_name = product.get('name') if product else None
                    product_description = product.get('description') if product else None
            
                    current_period_end = stripe_sub.get('current_period_end') or (
                        item.get('current_period_end') if item else None
                    )
                    if current_period_end:
                        current_period_end = datetime.fromtimestamp(current_period_end, tz=dt_timezone.utc)

                    interval = item.get('plan', {}).get('interval', 'unknown') if item else 'unknown'
                    interval_count = item.get('plan', {}).get('interval_count', 0) if item else 0
                    package_name = f"{product_name}_{interval}_{interval_count}"
                    unit_amount = price.get('unit_amount') / 100 if price and price.get('unit_amount') else None

                    Subscription.objects.create(
                        user=user,
                        stripe_customer_id=stripe_sub['customer'],
                        stripe_subscription_id=stripe_sub['id'],
                        package_name=package_name,
                        price_id=item['price']['id'] if item else None,
                        price=unit_amount,
                        status=stripe_sub['status'],
                        start_date=timezone.now(),
                        current_period_end=current_period_end,
                        cancel_at_period_end=stripe_sub.get('cancel_at_period_end', False),
                        latest_invoice=stripe_sub.get('latest_invoice'),
                        is_active=True
                    )

                elif event_type == 'customer.subscription.deleted':
                    sub_id = data['id']
                    sub = Subscription.objects.filter(stripe_subscription_id=sub_id).first()
                    if sub:
                        sub.is_active = False
                        sub.status = "canceled"
                        sub.end_date = timezone.now()
                        sub.save()

                elif event_type == 'customer.subscription.updated':
                    sub_id = data['id']
                    sub = Subscription.objects.filter(stripe_subscription_id=sub_id).first()
                    if sub:
                        current_period_end = data.get('current_period_end')
                        if current_period_end:
                            sub.current_period_end = datetime.fromtimestamp(current_period_end, tz=dt_timezone.utc)

                        sub.status = data.get('status', sub.status)
                        sub.cancel_at_period_end = data.get('cancel_at_period_end', sub.cancel_at_period_end)
                        sub.latest_invoice = data.get('latest_invoice', sub.latest_invoice)
                        sub.updated_at = timezone.now()
                        sub.save()

        except Exception as e:
            print(f"Webhook processing error: {e}")
            return JsonResponse({'error': str(e)}, status=500)

        return HttpResponse(status=200)
    




class CancelSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsMemberRole]

    @swagger_auto_schema(
        tags=["subscriptions"],
        operation_summary="Cancel active subscription",
        operation_description="Cancels the current active subscription for the logged-in user. This cancels it in Stripe and updates the local database.",
        responses={
            200: openapi.Response(description="Subscription cancelled successfully"),
            400: openapi.Response(description="No active subscription found"),
        }
    )
    def post(self, request, *args, **kwargs):
        user = request.user

        # Step 1: Find active subscription
        active_sub = Subscription.objects.filter(
            user=user,
            is_active=True,
            current_period_end__gt=timezone.now()
        ).first()

        if not active_sub:
            return Response({'error': 'No active subscription found.'}, status=400)

        try:
            # Step 2: Cancel subscription in Stripe (at period end)
            stripe.Subscription.modify(
                active_sub.stripe_subscription_id,
                cancel_at_period_end=True
            )

            # Step 3: Update local DB
            active_sub.cancel_at_period_end = True
            active_sub.is_active = False
            active_sub.updated_at = timezone.now()
            active_sub.save()

            return Response({'message': 'Subscription will be cancelled at the end of the billing period.'}, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=400)
        





class SubscriptionStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=["subscriptions"],
        operation_summary="Get current subscription status",
        operation_description="Returns the status and details of the user's current active subscription.",
        responses={
            200: openapi.Response(
                description="Subscription status retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'package_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'current_period_end': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'cancel_at_period_end': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            ),
            404: openapi.Response(description="No active subscription found"),
        }
    )
    def get(self, request, *args, **kwargs):
        user = request.user

        subscription = Subscription.objects.filter(
            user=user,
            is_active=True,
            current_period_end__gt=timezone.now()
        ).first()

        if not subscription:
            return Response({'detail': 'No active subscription found.'}, status=404)

        return Response({
            'package_name': subscription.package_name,
            'status': subscription.status,
            'current_period_end': subscription.current_period_end,
            'cancel_at_period_end': subscription.cancel_at_period_end,
        })
