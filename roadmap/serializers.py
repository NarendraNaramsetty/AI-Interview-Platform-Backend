from rest_framework import serializers
from .models import (
    CareerPath,
    Roadmap,
    RoadmapModule,
    LearningResource,
    UserRoadmap,
    ModuleProgress,
    LearningReminder
)
from .validators import validate_percentage_range, validate_reminder_time

# ----------------------------------------------------
# Request Payload Serializers
# ----------------------------------------------------

class StartRoadmapRequestSerializer(serializers.Serializer):
    roadmap_id = serializers.IntegerField(required=True)


class UpdateProgressRequestSerializer(serializers.Serializer):
    user_roadmap_id = serializers.IntegerField(required=True)
    module_id = serializers.IntegerField(required=True)
    is_completed = serializers.BooleanField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class RoadmapActionRequestSerializer(serializers.Serializer):
    roadmap_id = serializers.IntegerField(required=True)


# ----------------------------------------------------
# Model Representation Serializers
# ----------------------------------------------------

class CareerPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerPath
        fields = ['id', 'uuid', 'name', 'description', 'icon', 'estimated_duration', 'difficulty', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']


class LearningResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningResource
        fields = ['id', 'uuid', 'title', 'resource_type', 'provider', 'url', 'duration', 'is_free']
        read_only_fields = ['id', 'uuid']


class RoadmapModuleDetailSerializer(serializers.ModelSerializer):
    resources = LearningResourceSerializer(many=True, read_only=True)
    is_completed = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()

    class Meta:
        model = RoadmapModule
        fields = ['id', 'uuid', 'title', 'description', 'module_order', 'estimated_hours', 'module_type', 'resources', 'is_completed', 'notes']

    def get_is_completed(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            progress = obj.progresses.filter(user_roadmap__user=request.user).first()
            return progress.is_completed if progress else False
        return False

    def get_notes(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            progress = obj.progresses.filter(user_roadmap__user=request.user).first()
            return progress.notes if progress else ""
        return ""


class RoadmapSerializer(serializers.ModelSerializer):
    career_path_name = serializers.CharField(source='career_path.name', read_only=True)

    class Meta:
        model = Roadmap
        fields = ['id', 'uuid', 'title', 'description', 'career_path', 'career_path_name', 'estimated_duration', 'total_modules', 'difficulty', 'is_active', 'created_at']
        read_only_fields = ['id', 'uuid', 'total_modules', 'created_at']


class RoadmapDetailSerializer(serializers.ModelSerializer):
    career_path_name = serializers.CharField(source='career_path.name', read_only=True)
    modules = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Roadmap
        fields = ['id', 'uuid', 'title', 'description', 'career_path', 'career_path_name', 'estimated_duration', 'total_modules', 'difficulty', 'modules', 'progress', 'is_active']
        read_only_fields = ['id', 'uuid', 'total_modules']

    def get_modules(self, obj):
        modules = obj.modules.all()
        return RoadmapModuleDetailSerializer(modules, many=True, context=self.context).data

    def get_progress(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            user_roadmap = obj.user_progresses.filter(user=request.user).first()
            if user_roadmap:
                return {
                    "user_roadmap_id": user_roadmap.id,
                    "progress_percentage": user_roadmap.progress_percentage,
                    "completed_modules": user_roadmap.completed_modules,
                    "status": user_roadmap.status,
                    "current_module_id": user_roadmap.current_module_id
                }
        return None


class UserRoadmapSerializer(serializers.ModelSerializer):
    roadmap_title = serializers.CharField(source='roadmap.title', read_only=True)
    roadmap_details = RoadmapSerializer(source='roadmap', read_only=True)

    class Meta:
        model = UserRoadmap
        fields = ['id', 'uuid', 'user', 'roadmap', 'roadmap_title', 'roadmap_details', 'progress_percentage', 'completed_modules', 'current_module', 'started_at', 'completed_at', 'status']
        read_only_fields = ['id', 'uuid', 'user', 'progress_percentage', 'completed_modules', 'started_at', 'completed_at']


class ModuleProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleProgress
        fields = ['user_roadmap', 'roadmap_module', 'is_completed', 'completion_date', 'notes']
        read_only_fields = ['completion_date']


class LearningReminderSerializer(serializers.ModelSerializer):
    roadmap_title = serializers.CharField(source='roadmap.title', read_only=True)

    class Meta:
        model = LearningReminder
        fields = ['id', 'uuid', 'user', 'roadmap', 'roadmap_title', 'reminder_time', 'frequency', 'is_enabled']
        read_only_fields = ['id', 'uuid', 'user']
