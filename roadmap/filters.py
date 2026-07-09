import django_filters
from .models import Roadmap, LearningResource

class RoadmapFilter(django_filters.FilterSet):
    """
    Filter set supporting searches for roadmaps matching target difficulty levels or career paths.
    """
    career = django_filters.NumberFilter(field_name='career_path_id')
    difficulty = django_filters.CharFilter(field_name='difficulty')

    class Meta:
        model = Roadmap
        fields = ['career', 'difficulty']


class LearningResourceFilter(django_filters.FilterSet):
    """
    Filters learning resources based on free/paid tags, provider tags, or study formats.
    """
    type = django_filters.CharFilter(field_name='resource_type')
    provider = django_filters.CharFilter(field_name='provider')
    is_free = django_filters.BooleanFilter(field_name='is_free')

    class Meta:
        model = LearningResource
        fields = ['type', 'provider', 'is_free']
