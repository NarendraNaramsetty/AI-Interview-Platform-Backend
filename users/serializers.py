from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import UserProfile, UserStatistics, Achievement, UserAchievement, UserPreference
from .validators import validate_cgpa, validate_graduation_year

User = get_user_model()

class NestedUserSerializer(serializers.ModelSerializer):
    """
    Represent critical user fields nested inside profile payloads.
    """
    class Meta:
        model = User
        fields = ['id', 'uuid', 'first_name', 'last_name', 'email', 'profile_picture']
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializes complete UserProfile records, embedding basic user credentials.
    """
    user = NestedUserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'headline', 'current_role', 'experience_level',
            'preferred_job_role', 'preferred_company', 'preferred_interview_language',
            'target_package', 'education', 'university', 'graduation_year', 'cgpa',
            'skills', 'interests', 'github_url', 'linkedin_url', 'portfolio_url',
            'location', 'timezone', 'profile_completion_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'profile_completion_percentage', 'created_at', 'updated_at']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Validates and updates user profiles Career/Education credentials.
    """
    headline = serializers.CharField(required=False, allow_blank=True)
    education = serializers.CharField(required=False, allow_blank=True)
    university = serializers.CharField(required=False, allow_blank=True)
    cgpa = serializers.FloatField(required=False, allow_null=True, validators=[validate_cgpa])
    graduation_year = serializers.IntegerField(required=False, allow_null=True, validators=[validate_graduation_year])

    class Meta:
        model = UserProfile
        fields = [
            'headline', 'current_role', 'experience_level', 'preferred_job_role',
            'preferred_company', 'preferred_interview_language', 'target_package',
            'education', 'university', 'graduation_year', 'cgpa', 'interests',
            'github_url', 'linkedin_url', 'portfolio_url', 'location', 'timezone'
        ]


class AvatarUploadSerializer(serializers.Serializer):
    """
    Validates profile picture image uploads.
    """
    avatar = serializers.ImageField(required=True)

    def validate_avatar(self, value):
        max_size = 5 * 1024 * 1024  # 5 MB
        if value.size > max_size:
            raise serializers.ValidationError(_("Avatar size cannot exceed 5 MB limit."))
        
        allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
        extension = value.name.split('.')[-1].lower()
        if extension not in allowed_extensions:
            raise serializers.ValidationError(_("Only JPG, PNG, and WEBP files are supported."))
            
        return value


class UserStatisticsSerializer(serializers.ModelSerializer):
    """
    Serializes user platform performance metrics.
    """
    class Meta:
        model = UserStatistics
        fields = [
            'total_interviews', 'completed_interviews', 'coding_attempts',
            'coding_passed', 'resumes_uploaded', 'chatbot_questions',
            'roadmap_completed', 'average_score', 'highest_score',
            'current_streak', 'total_learning_hours'
        ]
        read_only_fields = fields


class AchievementSerializer(serializers.ModelSerializer):
    """
    Serializes global achievement configurations.
    """
    class Meta:
        model = Achievement
        fields = ['id', 'title', 'description', 'badge_icon', 'points', 'category']


class UserAchievementSerializer(serializers.ModelSerializer):
    """
    Serializes earning associations of unlocked badges.
    """
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = UserAchievement
        fields = ['id', 'achievement', 'earned_at']
        read_only_fields = ['id', 'achievement', 'earned_at']


class UserPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializes and updates user interface layout settings.
    """
    class Meta:
        model = UserPreference
        fields = [
            'dark_mode', 'email_notifications', 'push_notifications',
            'preferred_theme', 'interview_difficulty', 'preferred_roles',
            'preferred_companies', 'language', 'timezone'
        ]
        read_only_fields = []


class SkillItemSerializer(serializers.Serializer):
    """
    Serializes skills array elements: {"id": 1, "name": "Python"}
    """
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=100)


class PublicProfileSerializer(serializers.ModelSerializer):
    """
    Serializes public-safe user profiles, hiding sensitive data fields.
    """
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    profile_picture = serializers.ImageField(source='user.profile_picture', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'profile_picture', 'headline', 
            'current_role', 'experience_level', 'education', 'university', 
            'skills', 'interests', 'github_url', 'linkedin_url', 
            'portfolio_url', 'location'
        ]
        read_only_fields = fields

