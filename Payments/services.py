import uuid
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction

from .models import SubscriptionPlan, UserSubscription, PaymentTransaction
from .constants import SUB_ACTIVE, SUB_CANCELED, TXN_SUCCEEDED

class PaymentsService:
    """
    Handles checkout subscription activations, cancel renewals, webhook integrations,
    and payment history logging.
    """

    @classmethod
    def checkout_subscription(cls, plan_id: int, user) -> dict:
        """
        Generates checkout session URL redirect mapping. Injects a mock active subscription.
        """
        try:
            plan = SubscriptionPlan.objects.get(pk=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise ValidationError("Subscription plan not found or inactive.")

        with transaction.atomic():
            # Mock period duration: 30 days
            start = timezone.now()
            end = start + timezone.timedelta(days=30)

            # Deactivate previous active user subscriptions if any
            UserSubscription.objects.filter(user=user, status=SUB_ACTIVE).update(
                status=SUB_CANCELED,
                end_date=timezone.now()
            )

            # Create UserSubscription
            user_sub = UserSubscription.objects.create(
                user=user,
                plan=plan,
                status=SUB_ACTIVE,
                start_date=start,
                end_date=end,
                stripe_subscription_id=f"sub_mock_{uuid.uuid4().hex[:12]}",
                cancel_at_period_end=False
            )

            # Record Payment transaction
            PaymentTransaction.objects.create(
                user=user,
                subscription=user_sub,
                amount=plan.price,
                currency='USD',
                payment_status=TXN_SUCCEEDED,
                stripe_charge_id=f"ch_mock_{uuid.uuid4().hex[:12]}"
            )

        return {
            "checkout_url": f"https://checkout.stripe.com/pay/mock_cs_{uuid.uuid4().hex}",
            "subscription_id": user_sub.id,
            "plan_name": plan.name
        }

    @classmethod
    def cancel_subscription(cls, user) -> UserSubscription:
        """
        Flags user subscription renewal to stop at period end.
        """
        active_sub = UserSubscription.objects.filter(user=user, status=SUB_ACTIVE).first()
        if not active_sub:
            raise ValidationError("No active subscription found to cancel.")

        active_sub.cancel_at_period_end = True
        active_sub.save()
        return active_sub
