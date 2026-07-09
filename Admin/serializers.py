from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import UserProfile

User = get_user_model()

class AdminUserListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    target_role = serializers.CharField(source='preferred_job_role', read_only=True)
    ranking_points = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'email', 'first_name', 'last_name', 'target_role', 'experience_level', 'ranking_points']
        read_only_fields = fields

    def get_ranking_points(self, obj):
        if hasattr(obj.user, 'statistics'):
            return obj.user.statistics.highest_score
        return 0

