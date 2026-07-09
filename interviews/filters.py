import django_filters
from .models import InterviewSession

class InterviewSessionFilter(django_filters.FilterSet):
    """
    Search and filter criteria for InterviewSession querysets.
    """
    role = django_filters.CharFilter(field_name='target_role', lookup_expr='icontains', label='Target Role')
    company = django_filters.CharFilter(field_name='target_company', lookup_expr='icontains', label='Target Company')
    difficulty = django_filters.CharFilter(field_name='difficulty', lookup_expr='iexact', label='Difficulty')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact', label='Status')
    interview_type = django_filters.CharFilter(field_name='interview_type', lookup_expr='iexact', label='Interview Type')
    
    # Date bounds
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label='Created after')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label='Created before')

    class Meta:
        model = InterviewSession
        fields = ['difficulty', 'status', 'interview_type']
