import django_filters
from .models import Resume

class ResumeFilter(django_filters.FilterSet):
    """
    Search and filter fields for user Resume files.
    """
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains', label='Search by Title')
    is_default = django_filters.BooleanFilter(field_name='is_default', label='Is Default')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact', label='Status')
    upload_source = django_filters.CharFilter(field_name='upload_source', lookup_expr='iexact', label='Upload Source')
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label='Created after')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label='Created before')

    class Meta:
        model = Resume
        fields = ['is_default', 'status', 'upload_source']
