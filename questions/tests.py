from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import io

from .models import (
    InterviewQuestion,
    QuestionCategory,
    Company,
    JobRole,
    Topic,
    QuestionAttachment,
    QuestionHistory
)
from .services import QuestionBankService

User = get_user_model()

class QuestionBankModuleTests(APITestCase):
    """
    Unit test suite covering the Question Bank CRUD permissions,
    Excel imports/exports, cloner duplicates, attachments, and histories.
    """

    def setUp(self):
        # Create test users
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

        # Pre-populate category and question
        self.category = QuestionCategory.objects.create(
            name='Python',
            description='Python coding questions.'
        )
        self.topic = Topic.objects.create(
            category=self.category,
            name='OOP'
        )
        self.company = Company.objects.create(
            name='Google'
        )
        self.role = JobRole.objects.create(
            title='Backend Developer',
            experience_level='Junior',
            category=self.category
        )

        self.question = InterviewQuestion.objects.create(
            question="What is a Python decorator and how is it defined?",
            short_description="Python Decorators",
            category=self.category,
            topic=self.topic,
            company=self.company,
            role=self.role,
            difficulty='Medium',
            expected_duration=10,
            answer_type='Text',
            tags=['Python', 'Decorators'],
            created_by=self.admin
        )

        # URL paths
        self.questions_list_url = reverse('interview-question-list')
        self.questions_detail_url = reverse('interview-question-detail', args=[self.question.id])
        self.search_url = reverse('questions_search')
        self.random_url = reverse('questions_random')
        self.import_url = reverse('questions_import')
        self.export_url = reverse('questions_export')

    def test_permissions_read_only_for_candidates(self):
        # Candidates can read questions
        self.client.force_authenticate(user=self.candidate)
        response = self.client.get(self.questions_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Candidates cannot create categories
        category_url = reverse('category-list')
        response = self.client.post(category_url, {'name': 'Go'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Candidates cannot delete questions
        response = self.client.delete(self.questions_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_crud_success_for_admins(self):
        self.client.force_authenticate(user=self.admin)
        
        # Create category
        category_url = reverse('category-list')
        response = self.client.post(category_url, {'name': 'Golang', 'display_order': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(QuestionCategory.objects.filter(name='Golang').exists())

        # Create topic
        topic_url = reverse('topic-list')
        response = self.client.post(topic_url, {'category': self.category.id, 'name': 'Generics'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Update question details
        response = self.client.put(self.questions_detail_url, {
            'question': "Explain Python generators memory advantages.",
            'category': self.category.id,
            'difficulty': 'Hard',
            'expected_duration': 8,
            'answer_type': 'Text'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.question.refresh_from_db()
        self.assertEqual(self.question.difficulty, 'Hard')
        
        # Verify update history log triggered by signal
        self.assertTrue(QuestionHistory.objects.filter(question=self.question, action='Updated').exists())

    def test_duplicate_question(self):
        self.client.force_authenticate(user=self.admin)
        duplicate_url = reverse('question_duplicate', args=[self.question.id])
        
        response = self.client.post(duplicate_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        dup_id = response.data['data']['id']
        dup_question = InterviewQuestion.objects.get(id=dup_id)
        self.assertEqual(dup_question.difficulty, 'Medium')
        self.assertEqual(dup_question.category, self.category)
        
        # Verify parent audit history
        self.assertTrue(QuestionHistory.objects.filter(question=dup_question, action='Duplicated').exists())

    def test_random_questions_selection(self):
        self.client.force_authenticate(user=self.candidate)
        
        # Requests random questions matching category filter
        response = self.client.get(self.random_url, {'category_id': self.category.id, 'count': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)  # Only 1 question exists in database

    def test_bulk_csv_import(self):
        self.client.force_authenticate(user=self.admin)
        
        # Formulate CSV file content in memory
        csv_data = (
            "question,category,difficulty,expected_duration,topic,company,role\n"
            "Explain Python list comprehension syntax.,Python,Easy,5,OOP,Google,Backend Developer\n"
            "Explain decorators execution sequence.,Python,Medium,10,OOP,Google,Backend Developer\n"
        )
        csv_file = SimpleUploadedFile("import_questions.csv", csv_data.encode('utf-8'), content_type="text/csv")
        
        response = self.client.post(self.import_url, {'file': csv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        data = response.data['data']
        self.assertEqual(data['success_count'], 2)
        self.assertEqual(data['failed_count'], 0)
        
        # Verify questions loaded in database
        self.assertEqual(InterviewQuestion.objects.filter(category=self.category).count(), 3)

    def test_export_questions_to_csv(self):
        self.client.force_authenticate(user=self.candidate)
        
        response = self.client.get(self.export_url, {'export_format': 'csv'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        csv_content = response.content.decode('utf-8')
        self.assertIn('What is a Python decorator', csv_content)

    def test_question_attachments_management(self):
        self.client.force_authenticate(user=self.admin)
        attachments_url = reverse('question_attachments', args=[self.question.id])

        # Add image attachment file
        img_data = b"fake-binary-image-data-chunks"
        img_file = SimpleUploadedFile("diagram.png", img_data, content_type="image/png")
        
        response = self.client.post(attachments_url, {'file': img_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        attachment_id = response.data['data']['id']
        self.assertEqual(response.data['data']['file_type'], 'image/png')
        self.assertEqual(QuestionAttachment.objects.filter(question=self.question).count(), 1)

        # Read attachments list
        response = self.client.get(attachments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

        # Delete attachment file
        del_url = reverse('question_attachment_delete', args=[attachment_id])
        response = self.client.delete(del_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(QuestionAttachment.objects.filter(question=self.question).count(), 0)
