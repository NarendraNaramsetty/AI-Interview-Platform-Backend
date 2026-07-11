from rest_framework import serializers
from .models import (
    CodingSandboxSession, CodingChallengeResult, 
    InterviewSession, InterviewQuestionResult,
    ResumeAuditResult
)

# ... [keep previous serializer classes exactly unchanged] ...
class CodingChallengeResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodingChallengeResult
        fields = [
            'id', 'session', 'question_text', 'starter_code', 'test_cases',
            'user_submitted_code', 'ai_score', 'ai_feedback', 'status', 'created_at'
        ]

class CodingSandboxSessionSerializer(serializers.ModelSerializer):
    results = CodingChallengeResultSerializer(many=True, read_only=True)
    
    class Meta:
        model = CodingSandboxSession
        fields = [
            'id', 'user', 'language', 'questions_count', 'company_focus',
            'experience_tier', 'difficulty', 'created_at', 'results'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class InterviewQuestionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewQuestionResult
        fields = [
            'id', 'session', 'question_number', 'question_text', 'scenario_context',
            'skill_focus', 'difficulty_tag', 'expected_answer_points', 'user_answer',
            'ai_score', 'ai_feedback', 'status', 'created_at'
        ]


class InterviewSessionSerializer(serializers.ModelSerializer):
    questions = InterviewQuestionResultSerializer(many=True, read_only=True)
    
    class Meta:
        model = InterviewSession
        fields = [
            'id', 'user', 'target_role', 'experience_level', 'difficulty',
            'interview_mode', 'selected_skills', 'score_goal', 'total_questions',
            'ready_score', 'created_at', 'questions'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class ResumeAuditResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeAuditResult
        fields = [
            'id', 'user', 'original_filename', 'file_type', 'extracted_text',
            'target_role', 'overall_ats_score', 'category_scores', 'keyword_analysis',
            'formatting_issues', 'recommendations', 'detected_sections',
            'missing_sections', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']
