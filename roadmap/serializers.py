from rest_framework import serializers
from .models import (
    CareerPath,
    Roadmap,
    RoadmapModule,
    LearningResource,
    UserRoadmap,
    ModuleProgress,
    LearningReminder,
    RoadmapPathway,
    RoadmapMilestone
)
from .validators import validate_percentage_range, validate_reminder_time


class RoadmapMilestoneSerializer(serializers.ModelSerializer):
    """Serializer for individual roadmap milestones."""
    
    class Meta:
        model = RoadmapMilestone
        fields = [
            'id',
            'uuid',
            'milestone_number',
            'title',
            'difficulty_tag',
            'description',
            'why_it_matters',
            'estimated_hours',
            'key_topics',
            'is_completed',
            'progress_percent',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']


class RoadmapPathwaySerializer(serializers.ModelSerializer):
    """Serializer for roadmap pathways with nested milestones."""
    
    milestones = RoadmapMilestoneSerializer(many=True, read_only=True)
    total_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = RoadmapPathway
        fields = [
            'id',
            'uuid',
            'user_interest_text',
            'pathway_title',
            'inferred_starting_level',
            'inferred_level_reason',
            'overall_readiness_estimate_percent',
            'milestones',
            'total_hours',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'uuid',
            'pathway_title',
            'inferred_starting_level',
            'inferred_level_reason',
            'overall_readiness_estimate_percent',
            'milestones',
            'total_hours',
            'created_at',
            'updated_at',
        ]
    
    def get_total_hours(self, obj) -> int:
        """Calculate total estimated hours across all milestones."""
        return sum(m.estimated_hours for m in obj.milestones.all())


class RoadmapGenerateRequestSerializer(serializers.Serializer):
    """Serializer for roadmap generation request (input)."""
    
    interest = serializers.CharField(
        max_length=1000,
        help_text="What user wants to become/learn (e.g., 'QA Engineer')"
    )
    self_described_experience = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text="Optional: user's self-described background"
    )
    resume_context = serializers.CharField(
        max_length=2000,
        required=False,
        allow_blank=True,
        help_text="Optional: summary from connected resume"
    )


class MilestoneProgressUpdateSerializer(serializers.Serializer):
    """Serializer for updating milestone progress."""
    
    progress_percent = serializers.IntegerField(
        min_value=0,
        max_value=100,
        required=False,
        help_text="Update progress percentage"
    )
    is_completed = serializers.BooleanField(
        required=False,
        help_text="Mark as completed"
    )


class RoadmapPathwayListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing pathways without nested milestones."""
    
    milestone_count = serializers.SerializerMethodField()
    total_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = RoadmapPathway
        fields = [
            'id',
            'uuid',
            'pathway_title',
            'inferred_starting_level',
            'overall_readiness_estimate_percent',
            'milestone_count',
            'total_hours',
            'created_at',
        ]
    
    def get_milestone_count(self, obj) -> int:
        """Count of milestones."""
        return obj.milestones.count()
    
    def get_total_hours(self, obj) -> int:
        """Total estimated hours."""
        return sum(m.estimated_hours for m in obj.milestones.all())


class StartRoadmapRequestSerializer(serializers.Serializer):
    roadmap_id = serializers.IntegerField(required=True)


class UpdateProgressRequestSerializer(serializers.Serializer):
    user_roadmap_id = serializers.IntegerField(required=True)
    module_id = serializers.IntegerField(required=True)
    is_completed = serializers.BooleanField(required=False)
    is_bookmarked = serializers.BooleanField(required=False)
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
