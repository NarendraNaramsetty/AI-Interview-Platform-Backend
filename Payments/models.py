import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from .constants import (
    PLAN_CHOICES,
    PLAN_FREE,
    INTERVAL_CHOICES,
    INTERVAL_MONTHLY,
    SUB_STATUS_CHOICES,
    SUB_ACTIVE,
    TXN_STATUS_CHOICES,
    TXN_SUCCEEDED
)

class SubscriptionPlan(models.Model):
    """
    Available payment subscription levels (e.g. Free, Pro, Enterprise).
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_interval = models.CharField(
        max_length=50,
        choices=INTERVAL_CHOICES,
        default=INTERVAL_MONTHLY
    )
    features = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['price']
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return f"{self.name} - ${self.price}/{self.billing_interval}"


class UserSubscription(models.Model):
    """
    Tracks the active subscription tier and period dates for candidate users.
    """
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=50,
        choices=SUB_STATUS_CHOICES,
        default=SUB_ACTIVE
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"

    def __str__(self):
        return f"{self.user.email} -> {self.plan.name} ({self.status})"


class PaymentTransaction(models.Model):
    """
    Logs payment invoices, transaction outcomes, and Stripe references.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    payment_status = models.CharField(
        max_length=50,
        choices=TXN_STATUS_CHOICES,
        default=TXN_SUCCEEDED
    )
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"

    def __str__(self):
        return f"Txn {self.id} - {self.user.email} - ${self.amount} ({self.payment_status})"
