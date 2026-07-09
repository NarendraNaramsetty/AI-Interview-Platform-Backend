from django.urls import re_path
from .views import (
    SubscriptionPlanListView,
    CurrentSubscriptionView,
    CheckoutSubscriptionView,
    CancelSubscriptionView,
    PaymentsWebhookView
)

urlpatterns = [
    re_path(r'^plans/?$', SubscriptionPlanListView.as_view(), name='payments_plans'),
    re_path(r'^subscription/?$', CurrentSubscriptionView.as_view(), name='payments_subscription'),
    re_path(r'^checkout/?$', CheckoutSubscriptionView.as_view(), name='payments_checkout'),
    re_path(r'^subscription/cancel/?$', CancelSubscriptionView.as_view(), name='payments_cancel'),
    re_path(r'^webhook/?$', PaymentsWebhookView.as_view(), name='payments_webhook'),
]
