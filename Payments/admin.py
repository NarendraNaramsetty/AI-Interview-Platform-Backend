from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, PaymentTransaction

class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'billing_interval', 'is_active']
    list_filter = ['is_active', 'billing_interval']
    search_fields = ['name']


class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'plan', 'status', 'start_date', 'end_date', 'cancel_at_period_end']
    list_filter = ['status', 'cancel_at_period_end']
    search_fields = ['user__email', 'stripe_subscription_id']


class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'subscription', 'amount', 'currency', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'created_at']
    search_fields = ['user__email', 'stripe_charge_id']


admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(UserSubscription, UserSubscriptionAdmin)
admin.site.register(PaymentTransaction, PaymentTransactionAdmin)
