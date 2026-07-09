from rest_framework import serializers
from .models import Resume, ResumeAnalysis, ResumeActivity
from .validators import (
    validate_resume_file_extension,
    validate_resume_file_size,
    validate_file_corruption,
    validate_filename_chars
)

class ResumeAnalysisSerializer(serializers.ModelSerializer):
    """
    Serializes placeholder AI assessments associated with user resumes.
    """
    class Meta:
        model = ResumeAnalysis
        fields = [
            'id', 'overall_score', 'ats_score', 'grammar_score', 
            'keyword_score', 'completeness_score', 'summary', 
            'strengths', 'weaknesses', 'missing_skills', 
            'recommended_roles', 'analysis_status', 'created_at', 'updated_at'
        ]


class ResumeSerializer(serializers.ModelSerializer):
    """
    Standard serializer representing light metadata fields for Resume objects list.
    """
    class Meta:
        model = Resume
        fields = [
            'id', 'uuid', 'title', 'original_filename', 'file', 
            'file_size', 'file_type', 'resume_version', 'upload_source', 
            'status', 'processing_status', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class ResumeDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer including extracted raw text and nested analyses.
    """
    analysis = ResumeAnalysisSerializer(read_only=True)

    class Meta:
        model = Resume
        fields = [
            'id', 'uuid', 'title', 'original_filename', 'file', 
            'file_size', 'file_type', 'resume_version', 'resume_text', 
            'total_pages', 'upload_source', 'status', 'processing_status', 
            'is_default', 'analysis', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class ResumeUploadSerializer(serializers.Serializer):
    """
    Handles PDF/DOCX file upload parameters and runs robust corruption checks.
    """
    file = serializers.FileField(
        required=True,
        validators=[
            validate_resume_file_extension,
            validate_resume_file_size,
            validate_file_corruption
        ]
    )
    title = serializers.CharField(max_length=255, required=False, validators=[validate_filename_chars])
    upload_source = serializers.CharField(max_length=50, default='Web')


class ResumeUpdateSerializer(serializers.ModelSerializer):
    """
    Allows updating parameters like titles and replacement files.
    """
    title = serializers.CharField(max_length=255, required=False, validators=[validate_filename_chars])
    file = serializers.FileField(
        required=False,
        validators=[
            validate_resume_file_extension,
            validate_resume_file_size,
            validate_file_corruption
        ]
    )

    class Meta:
        model = Resume
        fields = ['title', 'file', 'is_default']


class ResumeActivitySerializer(serializers.ModelSerializer):
    """
    Serializes auditable resume transaction history logs.
    """
    class Meta:
        model = ResumeActivity
        fields = ['id', 'action', 'description', 'created_at']
        read_only_fields = fields
