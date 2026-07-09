from rest_framework import permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import SubscriptionPlan, UserSubscription
from .services import PaymentsService
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    CheckoutRequestSerializer
)
from .constants import SUB_ACTIVE

class SubscriptionPlanListView(generics.ListAPIView):
    """
    GET /api/payments/plans
    Lists all available, active subscription plans.
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Plans retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class CurrentSubscriptionView(APIView):
    """
    GET /api/payments/subscription
    Retrieves candidate current active subscription.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Active Subscription",
        responses={200: UserSubscriptionSerializer}
    )
    def get(self, request):
        sub = UserSubscription.objects.filter(user=request.user, status=SUB_ACTIVE).first()
        if not sub:
            return Response({
                "success": True,
                "message": "No active subscription found.",
                "data": None
            }, status=status.HTTP_200_OK)

        serializer = UserSubscriptionSerializer(sub)
        return Response({
            "success": True,
            "message": "Subscription retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class CheckoutSubscriptionView(APIView):
    """
    POST /api/payments/checkout
    Initiates payment subscription checkout.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Create Payment Checkout",
        request=CheckoutRequestSerializer,
        responses={201: OpenApiResponse(description="Checkout session details")}
    )
    def post(self, request):
        serializer = CheckoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan_id = serializer.validated_data['plan_id']

        try:
            res = PaymentsService.checkout_subscription(plan_id, request.user)
            return Response({
                "success": True,
                "message": "Checkout session initialized successfully.",
                "data": res
            }, status=status.HTTP_201_CREATED)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class CancelSubscriptionView(APIView):
    """
    POST /api/payments/subscription/cancel
    Cancel renewals at end of active period.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Cancel Subscription Renewal",
        responses={200: UserSubscriptionSerializer}
    )
    def post(self, request):
        try:
            sub = PaymentsService.cancel_subscription(request.user)
            serializer = UserSubscriptionSerializer(sub)
            return Response({
                "success": True,
                "message": "Subscription renewal cancelled successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class PaymentsWebhookView(APIView):
    """
    POST /api/payments/webhook
    Stripe Webhook simulation handler.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Stripe Webhook Handler",
        responses={200: OpenApiResponse(description="Webhook acknowledged")}
    )
    def post(self, request):
        # Acknowledge the webhook request
        return Response({
            "success": True,
            "message": "Webhook acknowledged.",
            "data": {}
        }, status=status.HTTP_200_OK)
