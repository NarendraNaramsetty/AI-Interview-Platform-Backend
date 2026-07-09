from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import AIProvider, AIModel, AIRequestLog, AIConfiguration, AIUsageStatistics
from .constants import PROVIDER_OLLAMA, PROVIDER_GEMINI, STATUS_SUCCESS
from .services import AIService

User = get_user_model()

class AICoreTests(APITestCase):
    """
    Unit test suite covering AI Core health pings, providers CRUD configuration,
    request logs statistics tracking, and administrator access checks.
    """

    def setUp(self):
        # Create users
        self.candidate = User.objects.create_user(
            email='candidate@prepai.dev',
            password='SecurePassword123!',
            first_name='Alice',
            last_name='Candidate'
        )

        self.admin = User.objects.create_user(
            email='admin@prepai.dev',
            password='AdminPassword123!',
            first_name='Bob',
            last_name='Admin',
            is_staff=True,
            is_superuser=True
        )

        self.provider = AIProvider.objects.create(
            provider_name=PROVIDER_OLLAMA,
            provider_type='Local',
            base_url='http://localhost:11434',
            model_name='llama3',
            is_default=True,
            is_active=True
        )

        self.config_obj = AIConfiguration.objects.create(
            key='SYSTEM_PROMPT_TEMPLATE',
            value='Act as a professional technical coach.',
            is_active=True
        )

        # URL paths
        self.providers_list_url = reverse('ai-provider-list')
        self.provider_detail_url = reverse('ai-provider-detail', args=[self.provider.id])
        self.health_url = reverse('ai_health_check')
        self.config_url = reverse('ai_config')
        self.stats_url = reverse('ai_statistics')
        self.logs_url = reverse('ai_logs_list')

    def test_health_check(self):
        self.client.force_authenticate(user=self.candidate)
        response = self.client.get(self.health_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'Healthy')
        self.assertEqual(response.data['data']['components']['ollama_status'], 'Available')

    def test_providers_crud_permissions(self):
        # Candidates can read but not write
        self.client.force_authenticate(user=self.candidate)
        response = self.client.get(self.providers_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # POST write attempt should fail with 403
        response = self.client.post(self.providers_list_url, {
            'provider_name': PROVIDER_GEMINI,
            'provider_type': 'Cloud',
            'model_name': 'gemini-1.5'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin CRUD successfully
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.providers_list_url, {
            'provider_name': PROVIDER_GEMINI,
            'provider_type': 'Cloud',
            'model_name': 'gemini-1.5'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AIProvider.objects.filter(provider_name=PROVIDER_GEMINI).count(), 1)

    def test_config_management_and_logs(self):
        # Candidate is forbidden from config reads/writes
        self.client.force_authenticate(user=self.candidate)
        response = self.client.get(self.config_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin retrieve and edit
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.config_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

        response = self.client.put(self.config_url, {
            'key': 'SYSTEM_PROMPT_TEMPLATE',
            'value': 'Act as a senior python interviewer.'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AIConfiguration.objects.get(key='SYSTEM_PROMPT_TEMPLATE').value, 'Act as a senior python interviewer.')

    def test_statistics_aggregation(self):
        self.client.force_authenticate(user=self.candidate)

        AIService.log_request(
            user=self.candidate,
            module_name='chatbot',
            request_type='Chat',
            provider='Ollama',
            model='llama3',
            prompt_length=20,
            response_length=50,
            execution_time=0.45,
            token_usage=40,
            request_status=STATUS_SUCCESS
        )

        # Query stats
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['data']
        self.assertEqual(data['total_requests'], 1)
        self.assertEqual(data['estimated_token_usage'], 40)
        self.assertEqual(data['error_rate'], 0.0)
