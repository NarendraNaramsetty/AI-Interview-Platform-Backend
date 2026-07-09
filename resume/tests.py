from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from unittest.mock import patch
import os

from .models import Resume, ResumeActivity, ResumeAnalysis
from .services import ResumeService

User = get_user_model()

class ResumeModuleTests(APITestCase):
    """
    Unit test suite covering resume uploads, versioning, soft deletion,
    default tagging, download streams, and access permissions.
    """

    def setUp(self):
        # Start corruption bypass mock patcher
        self.corruption_patcher = patch('resume.serializers.validate_file_corruption', return_value=None)
        self.corruption_patcher.start()

        # Create test users
        self.user1 = User.objects.create_user(
            email='alice@prepai.dev',
            password='SecurePassword123!',
            first_name='Alice',
            last_name='Developer'
        )
        self.user2 = User.objects.create_user(
            email='bob@prepai.dev',
            password='SecurePassword456!',
            first_name='Bob',
            last_name='Architect'
        )

        # URL paths
        self.list_url = reverse('resume_list')
        self.upload_url = reverse('resume_upload')
        
        # Create mock PDF file
        self.mock_pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        self.mock_file = SimpleUploadedFile("resume.pdf", self.mock_pdf_content, content_type="application/pdf")

    def tearDown(self):
        self.corruption_patcher.stop()

    @patch('resume.services.parse_resume_document', return_value=("Alice Backend Developer Skills", 2))
    def test_resume_upload_success(self, mock_parse):
        self.client.force_authenticate(user=self.user1)
        data = {
            'file': self.mock_file,
            'title': 'Alice Main Resume',
            'upload_source': 'Web'
        }
        response = self.client.post(self.upload_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        resume_data = response.data['data']
        self.assertEqual(resume_data['title'], 'Alice Main Resume')
        self.assertEqual(resume_data['total_pages'], 2)
        self.assertEqual(resume_data['resume_text'], 'Alice Backend Developer Skills')
        self.assertEqual(resume_data['processing_status'], 'Completed')

    @patch('resume.services.parse_resume_document', return_value=("Alice Resume", 2))
    def test_resume_upload_duplicate_file_hash(self, mock_parse):
        self.client.force_authenticate(user=self.user1)
        
        # Upload once
        ResumeService.process_new_resume(
            user=self.user1,
            title='Alice Resume 1',
            uploaded_file=self.mock_file
        )
        
        # Upload second time (exact same file)
        self.mock_file.seek(0)
        data = {'file': self.mock_file, 'title': 'Alice Resume 2'}
        response = self.client.post(self.upload_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    @patch('resume.services.parse_resume_document', return_value=("Alice Skills", 1))
    def test_set_default_resume(self, mock_parse):
        self.client.force_authenticate(user=self.user1)
        
        # Create two resumes
        res1 = ResumeService.process_new_resume(self.user1, 'Resume 1', self.mock_file)
        self.mock_file.seek(0)
        
        # Change content hash slightly to prevent duplicate block
        mock_file_2 = SimpleUploadedFile("resume2.pdf", self.mock_pdf_content + b"extra", content_type="application/pdf")
        res2 = ResumeService.process_new_resume(self.user1, 'Resume 2', mock_file_2)
        
        # Set res2 as default
        default_url = reverse('resume_set_default', args=[res2.id])
        response = self.client.post(default_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        res1.refresh_from_db()
        res2.refresh_from_db()
        self.assertFalse(res1.is_default)
        self.assertTrue(res2.is_default)

    @patch('resume.services.parse_resume_document', return_value=("Alice Text", 1))
    def test_resume_soft_delete(self, mock_parse):
        self.client.force_authenticate(user=self.user1)
        res = ResumeService.process_new_resume(self.user1, 'Resume To Delete', self.mock_file)
        
        delete_url = reverse('resume_detail', args=[res.id])
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify it is omitted in active listing
        self.assertEqual(Resume.objects.filter(id=res.id).count(), 0)
        
        # Verify it still exists in deleted queries
        self.assertEqual(Resume.objects.all_with_deleted().filter(id=res.id).count(), 1)
        deleted_res = Resume.objects.all_with_deleted().get(id=res.id)
        self.assertIsNotNone(deleted_res.deleted_at)

    @patch('resume.services.parse_resume_document', return_value=("Alice Text", 1))
    def test_resume_details_owner_permissions(self, mock_parse):
        # Alice uploads a resume
        res = ResumeService.process_new_resume(self.user1, 'Alice Secret Resume', self.mock_file)
        
        # Bob tries to access Alice's resume
        self.client.force_authenticate(user=self.user2)
        detail_url = reverse('resume_detail', args=[res.id])
        response = self.client.get(detail_url)
        # Should be forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('resume.services.parse_resume_document', return_value=("Alice Text v1", 1))
    def test_resume_replace_file_increments_version(self, mock_parse):
        self.client.force_authenticate(user=self.user1)
        res = ResumeService.process_new_resume(self.user1, 'Alice Resume', self.mock_file)
        self.assertEqual(res.resume_version, 1)

        # Perform update replacement file
        mock_file_replacement = SimpleUploadedFile(
            "resume.pdf", 
            self.mock_pdf_content + b"v2_updates", 
            content_type="application/pdf"
        )
        
        # Mock parsing response update
        with patch('resume.services.parse_resume_document', return_value=("Alice Text v2", 1)):
            detail_url = reverse('resume_detail', args=[res.id])
            response = self.client.put(detail_url, {'file': mock_file_replacement}, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            res.refresh_from_db()
            self.assertEqual(res.resume_version, 2)
            self.assertEqual(res.resume_text, "Alice Text v2")

    @patch('resume.services.parse_resume_document', return_value=("Alice Text", 1))
    def test_resume_activity_logs(self, mock_parse):
        self.client.force_authenticate(user=self.user1)
        res = ResumeService.process_new_resume(self.user1, 'Auditable Resume', self.mock_file)
        
        activity_url = reverse('resume_activity', args=[res.id])
        response = self.client.get(activity_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should show Uploaded Resume action
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['action'], 'Uploaded Resume')
