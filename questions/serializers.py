from rest_framework import serializers
from .models import (
    QuestionCategory,
    Company,
    JobRole,
    Topic,
    QuestionTag,
    InterviewQuestion,
    QuestionAttachment,
    QuestionHistory
)
from .validators import validate_question_text_length, validate_expected_duration, validate_import_file_format
from .constants import DIFFICULTY_CHOICES, SOURCE_CHOICES, ANSWER_TYPE_CHOICES_LIST

class QuestionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionCategory
        fields = ['id', 'uuid', 'name', 'description', 'icon', 'display_order', 'is_active', 'created_at', 'updated_at']


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'uuid', 'name', 'logo', 'website', 'description', 'is_active']


class JobRoleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = JobRole
        fields = ['id', 'uuid', 'title', 'description', 'experience_level', 'category', 'category_name']


class TopicSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Topic
        fields = ['id', 'uuid', 'category', 'category_name', 'name', 'description']


class QuestionTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionTag
        fields = ['name', 'color']


class QuestionAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAttachment
        fields = ['id', 'question', 'file', 'file_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class QuestionHistorySerializer(serializers.ModelSerializer):
    performed_by_email = serializers.EmailField(source='performed_by.email', read_only=True)

    class Meta:
        model = QuestionHistory
        fields = ['id', 'question', 'action', 'description', 'performed_by_email', 'timestamp']


class InterviewQuestionSerializer(serializers.ModelSerializer):
    category_details = QuestionCategorySerializer(source='category', read_only=True)
    topic_details = TopicSerializer(source='topic', read_only=True)
    company_details = CompanySerializer(source='company', read_only=True)
    role_details = JobRoleSerializer(source='role', read_only=True)
    attachments = QuestionAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = InterviewQuestion
        fields = [
            'id', 'uuid', 'question', 'short_description', 'category', 'category_details',
            'topic', 'topic_details', 'company', 'company_details', 'role', 'role_details',
            'difficulty', 'expected_duration', 'answer_type', 'tags', 'hints', 'reference_links',
            'expected_answer', 'explanation', 'source', 'is_active', 'created_by', 'attachments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'created_by', 'created_at', 'updated_at']


class InterviewQuestionWriteSerializer(serializers.ModelSerializer):
    question = serializers.CharField(validators=[validate_question_text_length])
    expected_duration = serializers.IntegerField(validators=[validate_expected_duration])

    class Meta:
        model = InterviewQuestion
        fields = [
            'question', 'short_description', 'category', 'topic', 'company', 'role',
            'difficulty', 'expected_duration', 'answer_type', 'tags', 'hints', 'reference_links',
            'expected_answer', 'explanation', 'source', 'is_active'
        ]

    def validate(self, data):
        # Validate that the category matches the topic's category
        topic = data.get('topic')
        category = data.get('category')
        if topic and category and topic.category != category:
            raise serializers.ValidationError(
                {"topic": "The selected topic must belong to the selected question category."}
            )
        return data


class ImportQuestionsSerializer(serializers.Serializer):
    file = serializers.FileField(required=True, validators=[validate_import_file_format])


class RandomQuestionsRequestSerializer(serializers.Serializer):
    category_id = serializers.IntegerField(required=False, allow_null=True)
    difficulty = serializers.ChoiceField(choices=DIFFICULTY_CHOICES, required=False, allow_blank=True, allow_null=True)
    company_id = serializers.IntegerField(required=False, allow_null=True)
    role_id = serializers.IntegerField(required=False, allow_null=True)
    count = serializers.IntegerField(required=False, default=5, min_value=1, max_value=30)
