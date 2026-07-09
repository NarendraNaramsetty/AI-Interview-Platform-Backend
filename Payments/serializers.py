from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription, PaymentTransaction

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'uuid', 'name', 'price', 'billing_interval', 'features', 'is_active']
        read_only_fields = ['id', 'uuid']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = UserSubscription
        fields = ['id', 'plan', 'status', 'start_date', 'end_date', 'stripe_subscription_id', 'cancel_at_period_end']
        read_only_fields = ['id', 'plan', 'status', 'start_date', 'end_date', 'stripe_subscription_id', 'cancel_at_period_end']


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ['id', 'uuid', 'amount', 'currency', 'payment_status', 'stripe_charge_id', 'created_at']
        read_only_fields = ['id', 'uuid', 'amount', 'currency', 'payment_status', 'stripe_charge_id', 'created_at']


class CheckoutRequestSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField(required=True)
