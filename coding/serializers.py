from rest_framework import serializers
from .models import (
    CodingCategory,
    CodingProblem,
    TestCase,
    CodeSubmission,
    CodingScore,
    CodingHistory,
    FavoriteProblem
)
from .validators import (
    validate_programming_language,
    validate_source_code_length
)

class StartSessionRequestSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField(required=True)


class SaveDraftRequestSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField(required=True)
    programming_language = serializers.CharField(required=True, validators=[validate_programming_language])
    source_code = serializers.CharField(required=True, validators=[validate_source_code_length])


class SubmitCodeRequestSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField(required=True)
    programming_language = serializers.CharField(required=True, validators=[validate_programming_language])
    source_code = serializers.CharField(required=True, validators=[validate_source_code_length])


class CodingCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CodingCategory
        fields = ['id', 'uuid', 'name', 'description', 'display_order', 'is_active', 'created_at']
        read_only_fields = ['id', 'uuid', 'created_at']


class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ['id', 'input_data', 'expected_output', 'is_sample']
        read_only_fields = ['id']


class CodingProblemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = CodingProblem
        fields = [
            'id', 'uuid', 'title', 'slug', 'difficulty', 'category', 'category_name',
            'company', 'company_name', 'tags', 'acceptance_rate', 'points', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'uuid', 'slug', 'acceptance_rate', 'created_at']


class CodingProblemDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    sample_test_cases = serializers.SerializerMethodField()

    class Meta:
        model = CodingProblem
        fields = [
            'id', 'uuid', 'title', 'slug', 'description', 'problem_statement',
            'input_format', 'output_format', 'constraints', 'sample_input', 'sample_output',
            'explanation', 'difficulty', 'category', 'category_name', 'company', 'company_name',
            'tags', 'hints', 'time_limit', 'memory_limit', 'acceptance_rate', 'points',
            'sample_test_cases', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'slug', 'acceptance_rate', 'created_at', 'updated_at']

    def get_sample_test_cases(self, obj):
        # Retrieve only public/sample test cases
        samples = obj.test_cases.filter(is_sample=True)
        return TestCaseSerializer(samples, many=True).data


class CodingScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodingScore
        fields = ['id', 'score', 'percentage', 'ranking_points', 'feedback_placeholder']
        read_only_fields = ['id']


class CodingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CodingHistory
        fields = ['id', 'action', 'description', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class CodeSubmissionSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    score_record = CodingScoreSerializer(read_only=True)
    history_logs = CodingHistorySerializer(many=True, read_only=True)

    class Meta:
        model = CodeSubmission
        fields = [
            'id', 'uuid', 'user', 'problem', 'problem_title', 'programming_language', 
            'source_code', 'execution_time', 'memory_used', 'passed_test_cases', 
            'total_test_cases', 'status', 'score_record', 'history_logs', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'uuid', 'user', 'execution_time', 'memory_used', 'passed_test_cases', 
            'total_test_cases', 'status', 'created_at', 'updated_at'
        ]


class FavoriteProblemSerializer(serializers.ModelSerializer):
    problem_details = CodingProblemSerializer(source='problem', read_only=True)

    class Meta:
        model = FavoriteProblem
        fields = ['id', 'user', 'problem', 'problem_details', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
