from rest_framework import serializers
from .models import (
    InterviewEvaluation,
    TechnicalEvaluation,
    CommunicationEvaluation,
    HRBehaviorEvaluation,
    OverallEvaluation,
    ImprovementSuggestion,
    RecommendedResource,
    EvaluationHistory
)
from .validators import (
    validate_score_range,
    validate_feedback_length,
    validate_suggestion_priority,
    validate_resource_url
)

class GenerateEvaluationRequestSerializer(serializers.Serializer):
    """
    Request payload format to trigger placeholder report cards generation.
    """
    interview_id = serializers.IntegerField(required=True)


class TechnicalEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalEvaluation
        fields = [
            'id', 'technical_score', 'coding_score', 'problem_solving_score', 
            'database_score', 'algorithm_score', 'explanation_quality',
            'strengths', 'weaknesses', 'recommendations'
        ]
        read_only_fields = ['id']

    def validate_technical_score(self, value):
        validate_score_range(value)
        return value

    def validate_coding_score(self, value):
        validate_score_range(value)
        return value

    def validate_problem_solving_score(self, value):
        validate_score_range(value)
        return value

    def validate_database_score(self, value):
        validate_score_range(value)
        return value

    def validate_algorithm_score(self, value):
        validate_score_range(value)
        return value

    def validate_explanation_quality(self, value):
        validate_score_range(value)
        return value


class CommunicationEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationEvaluation
        fields = [
            'id', 'communication_score', 'grammar_score', 'fluency_score', 
            'vocabulary_score', 'clarity_score', 'pronunciation_score_placeholder', 
            'confidence_score_placeholder'
        ]
        read_only_fields = ['id']

    def validate_communication_score(self, value):
        validate_score_range(value)
        return value

    def validate_grammar_score(self, value):
        validate_score_range(value)
        return value

    def validate_fluency_score(self, value):
        validate_score_range(value)
        return value

    def validate_vocabulary_score(self, value):
        validate_score_range(value)
        return value

    def validate_clarity_score(self, value):
        validate_score_range(value)
        return value


class HRBehaviorEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HRBehaviorEvaluation
        fields = [
            'id', 'confidence_score', 'professionalism_score', 'leadership_score', 
            'teamwork_score', 'adaptability_score', 'attitude_score', 'behavioral_feedback'
        ]
        read_only_fields = ['id']

    def validate_confidence_score(self, value):
        validate_score_range(value)
        return value

    def validate_professionalism_score(self, value):
        validate_score_range(value)
        return value

    def validate_leadership_score(self, value):
        validate_score_range(value)
        return value

    def validate_teamwork_score(self, value):
        validate_score_range(value)
        return value

    def validate_adaptability_score(self, value):
        validate_score_range(value)
        return value

    def validate_attitude_score(self, value):
        validate_score_range(value)
        return value


class OverallEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OverallEvaluation
        fields = [
            'id', 'overall_score', 'overall_rating', 'recommendation', 
            'final_feedback', 'next_learning_plan'
        ]
        read_only_fields = ['id']

    def validate_overall_score(self, value):
        validate_score_range(value)
        return value


class ImprovementSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImprovementSuggestion
        fields = ['id', 'evaluation', 'category', 'title', 'description', 'priority']
        read_only_fields = ['id']

    def validate_description(self, value):
        validate_feedback_length(value)
        return value

    def validate_priority(self, value):
        validate_suggestion_priority(value)
        return value


class RecommendedResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendedResource
        fields = ['id', 'evaluation', 'title', 'type', 'url', 'description']
        read_only_fields = ['id']

    def validate_url(self, value):
        validate_resource_url(value)
        return value


class EvaluationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationHistory
        fields = ['id', 'action', 'description', 'performed_at']
        read_only_fields = ['id', 'performed_at']


class InterviewEvaluationSerializer(serializers.ModelSerializer):
    """
    Representation structure containing scores, suggested adjustments, recommended courses, and change logs.
    """
    technical_evaluation = TechnicalEvaluationSerializer(read_only=True)
    communication_evaluation = CommunicationEvaluationSerializer(read_only=True)
    hr_evaluation = HRBehaviorEvaluationSerializer(read_only=True)
    overall_evaluation = OverallEvaluationSerializer(read_only=True)
    suggestions = ImprovementSuggestionSerializer(many=True, read_only=True)
    resources = RecommendedResourceSerializer(many=True, read_only=True)
    history_logs = EvaluationHistorySerializer(many=True, read_only=True)

    class Meta:
        model = InterviewEvaluation
        fields = [
            'id', 'uuid', 'interview', 'user', 'evaluation_status', 'evaluated_at',
            'technical_evaluation', 'communication_evaluation', 'hr_evaluation', 
            'overall_evaluation', 'suggestions', 'resources', 'history_logs', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'interview', 'user', 'evaluation_status', 'evaluated_at', 'created_at', 'updated_at']
