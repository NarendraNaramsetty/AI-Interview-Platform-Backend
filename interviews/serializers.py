from rest_framework import serializers
from .models import (
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    InterviewProgress,
    InterviewResult,
    InterviewTimeline
)
from resume.models import Resume
from .validators import validate_question_count, validate_duration_range, validate_audio_file_size
from .constants import DIFFICULTY_CHOICES, INTERVIEW_TYPE_CHOICES, MODE_CHOICES

class InterviewQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewQuestion
        fields = [
            'id', 'sequence_number', 'question_text', 'topic', 
            'category', 'difficulty', 'source', 'expected_answer_placeholder'
        ]


class InterviewAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewAnswer
        fields = ['id', 'question', 'answer_text', 'answer_type', 'audio_file', 'answer_duration', 'submitted_at']


class InterviewProgressSerializer(serializers.ModelSerializer):
    current_question_details = InterviewQuestionSerializer(source='current_question', read_only=True)

    class Meta:
        model = InterviewProgress
        fields = [
            'percentage_completed', 'current_question', 'current_question_details',
            'remaining_questions', 'elapsed_time', 'estimated_remaining_time', 'last_saved_at'
        ]


class InterviewResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewResult
        fields = [
            'technical_score', 'communication_score', 'confidence_score',
            'grammar_score', 'overall_score', 'status', 'feedback_placeholder', 'created_at'
        ]


class InterviewTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewTimeline
        fields = ['id', 'action', 'description', 'timestamp']


class InterviewSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewSession
        fields = [
            'id', 'uuid', 'title', 'target_role', 'target_company', 'interview_type',
            'difficulty', 'interview_mode', 'language', 'total_questions', 'answered_questions',
            'current_question_index', 'duration_minutes', 'elapsed_time_seconds', 'status',
            'started_at', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class StartInterviewSerializer(serializers.Serializer):
    resume_id = serializers.IntegerField(required=False, allow_null=True)
    target_role = serializers.CharField(max_length=255, required=True)
    target_company = serializers.CharField(max_length=255, required=True)
    interview_type = serializers.ChoiceField(choices=INTERVIEW_TYPE_CHOICES, required=True)
    difficulty = serializers.ChoiceField(choices=DIFFICULTY_CHOICES, required=True)
    interview_mode = serializers.ChoiceField(choices=MODE_CHOICES, required=True)
    language = serializers.CharField(max_length=100, default='English')
    total_questions = serializers.IntegerField(validators=[validate_question_count], default=5)
    duration_minutes = serializers.IntegerField(validators=[validate_duration_range], default=30)

    def validate_resume_id(self, value):
        if value:
            # Check ownership and soft deletion using accounts/resume models
            user = self.context.get('request').user
            if not Resume.objects.filter(id=value, user=user).exists():
                raise serializers.ValidationError("Resume does not exist or does not belong to you.")
        return value


class SaveAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(required=True)
    answer_text = serializers.CharField(required=True, allow_blank=True)
    audio_file = serializers.FileField(required=False, validators=[validate_audio_file_size], allow_null=True)
    answer_duration = serializers.IntegerField(required=True, min_value=0)  # Seconds

    def validate_question_id(self, value):
        session_id = self.context.get('session_id')
        if not InterviewQuestion.objects.filter(id=value, session_id=session_id).exists():
            raise serializers.ValidationError("Question ID does not belong to this interview session.")
        return value


class InterviewDetailSerializer(serializers.ModelSerializer):
    questions = InterviewQuestionSerializer(many=True, read_only=True)
    answers = InterviewAnswerSerializer(many=True, read_only=True)
    timeline_events = InterviewTimelineSerializer(many=True, read_only=True)
    result = InterviewResultSerializer(read_only=True)
    resume_details = serializers.SerializerMethodField()

    class Meta:
        model = InterviewSession
        fields = [
            'id', 'uuid', 'title', 'target_role', 'target_company', 'interview_type',
            'difficulty', 'interview_mode', 'language', 'total_questions', 'answered_questions',
            'current_question_index', 'duration_minutes', 'elapsed_time_seconds', 'status',
            'started_at', 'completed_at', 'questions', 'answers', 'timeline_events', 'result',
            'resume_details', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_resume_details(self, obj):
        if obj.resume:
            return {
                "id": obj.resume.id,
                "uuid": obj.resume.uuid,
                "title": obj.resume.title,
                "original_filename": obj.resume.original_filename
            }
        return None
