from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import SubscriptionPlan, UserSubscription, PaymentTransaction
from .constants import SUB_ACTIVE, SUB_CANCELED, PLAN_PRO

User = get_user_model()

class PaymentsTests(APITestCase):
    """
    Unit tests for payment subscription checking, stripe checkouts, and cancellations.
    """

    def setUp(self):
        self.candidate = User.objects.create_user(
            email='candidate@prepai.dev',
            password='SecurePassword123!',
            first_name='Alice',
            last_name='Candidate'
        )

        self.plan = SubscriptionPlan.objects.create(
            name=PLAN_PRO,
            price=29.99,
            billing_interval='Monthly',
            features={"chatbot": True, "interviews": 10},
            is_active=True
        )

        self.plans_url = reverse('payments_plans')
        self.sub_url = reverse('payments_subscription')
        self.checkout_url = reverse('payments_checkout')
        self.cancel_url = reverse('payments_cancel')
        self.webhook_url = reverse('payments_webhook')

    def test_plans_list(self):
        self.client.force_authenticate(user=self.candidate)
        response = self.client.get(self.plans_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['name'], PLAN_PRO)

    def test_checkout_and_cancel_subscription(self):
        self.client.force_authenticate(user=self.candidate)

        # 1. Checkout session
        response = self.client.post(self.checkout_url, {'plan_id': self.plan.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('checkout_url', response.data['data'])

        # 2. Get current active subscription
        response = self.client.get(self.sub_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['plan']['name'], PLAN_PRO)
        self.assertFalse(response.data['data']['cancel_at_period_end'])

        # 3. Cancel renewal
        response = self.client.post(self.cancel_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['cancel_at_period_end'])

    def test_webhook_acknowledgement(self):
        response = self.client.post(self.webhook_url, {'event': 'charge.succeeded'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
