from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import CustomUser
from .services import AuthService

class AuthenticationTests(APITestCase):
    """
    Unit test suite covering registrations, JWT logins, tokens blacklist,
    profile updates, permissions, and OTP reset channels.
    """

    def setUp(self):
        self.register_url = reverse('auth_register')
        self.login_url = reverse('auth_login')
        self.logout_url = reverse('auth_logout')
        self.profile_url = reverse('auth_profile_update')
        self.me_url = reverse('auth_me')
        self.forgot_pw_url = reverse('auth_forgot_password')
        self.verify_otp_url = reverse('auth_verify_otp')
        self.reset_pw_url = reverse('auth_reset_password')
        self.change_pw_url = reverse('auth_change_password')
        
        # Default user setup for login checks
        self.user_email = 'testuser@prepai.dev'
        self.user_password = 'SecurePassword123!'
        self.user = CustomUser.objects.create_user(
            email=self.user_email,
            password=self.user_password,
            first_name='Test',
            last_name='User'
        )

    def test_registration_successful(self):
        data = {
            'email': 'newuser@prepai.dev',
            'first_name': 'New',
            'last_name': 'Developer',
            'password': 'StrongPassword456!',
            'password_confirm': 'StrongPassword456!',
            'phone_number': '+1234567890',
            'country': 'Canada'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['user']['email'], 'newuser@prepai.dev')
        self.assertIn('tokens', response.data['data'])

    def test_registration_mismatched_password(self):
        data = {
            'email': 'badpass@prepai.dev',
            'first_name': 'Bad',
            'last_name': 'Password',
            'password': 'StrongPassword123!',
            'password_confirm': 'MismatchedPassword!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('password_confirm', response.data['errors'])

    def test_registration_weak_password(self):
        data = {
            'email': 'weakpass@prepai.dev',
            'first_name': 'Weak',
            'last_name': 'Password',
            'password': '123',
            'password_confirm': '123',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('password', response.data['errors'])

    def test_login_successful(self):
        data = {
            'email': self.user_email,
            'password': self.user_password
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access', response.data['data']['tokens'])

    def test_login_invalid_credentials(self):
        data = {
            'email': self.user_email,
            'password': 'WrongPassword1!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_logout_blacklisting(self):
        # Authenticate first
        login_response = self.client.post(self.login_url, {
            'email': self.user_email,
            'password': self.user_password
        })
        access_token = login_response.data['data']['tokens']['access']
        refresh_token = login_response.data['data']['tokens']['refresh']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Request logout
        response = self.client.post(self.logout_url, {'refresh': refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_me_endpoint_requires_auth(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint_successful(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['email'], self.user_email)

    def test_profile_update_successful(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'bio': 'Updated test bio info.',
            'country': 'France',
            'linkedin_url': 'https://linkedin.com/in/testuser'
        }
        response = self.client.put(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['bio'], 'Updated test bio info.')
        self.assertEqual(response.data['data']['country'], 'France')
        self.assertEqual(response.data['data']['linkedin_url'], 'https://linkedin.com/in/testuser')

    def test_change_password_successful(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'old_password': self.user_password,
            'new_password': 'NewSecurePassword123!',
            'password_confirm': 'NewSecurePassword123!'
        }
        response = self.client.post(self.change_pw_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_forgot_password_triggers_otp(self):
        response = self.client.post(self.forgot_pw_url, {'email': self.user_email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify OTP was written on user instance
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.otp_code)
        self.assertEqual(len(self.user.otp_code), 6)

    def test_verify_otp_valid(self):
        otp = AuthService.set_user_otp(self.user)
        data = {
            'email': self.user_email,
            'otp': otp
        }
        response = self.client.post(self.verify_otp_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_verify_otp_expired(self):
        otp = AuthService.set_user_otp(self.user)
        
        # Artificially expire the OTP
        self.user.otp_created_at = timezone.now() - timedelta(minutes=15)
        self.user.save()
        
        data = {
            'email': self.user_email,
            'otp': otp
        }
        response = self.client.post(self.verify_otp_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_reset_password_workflow_successful(self):
        otp = AuthService.set_user_otp(self.user)
        
        data = {
            'email': self.user_email,
            'otp': otp,
            'new_password': 'ResetSecurePassword456!',
            'password_confirm': 'ResetSecurePassword456!'
        }
        response = self.client.post(self.reset_pw_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_profile_avatar_upload_oversized_blocks(self):
        self.client.force_authenticate(user=self.user)
        
        # Create a mock file exceeding 5MB
        oversized_content = b"0" * (6 * 1024 * 1024)  # 6 MB
        large_file = SimpleUploadedFile("avatar.png", oversized_content, content_type="image/png")
        
        response = self.client.put(self.profile_url, {'profile_picture': large_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('profile_picture', response.data['errors'])
