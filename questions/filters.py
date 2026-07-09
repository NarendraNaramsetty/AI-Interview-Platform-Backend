import django_filters
from .models import InterviewQuestion

class InterviewQuestionFilter(django_filters.FilterSet):
    """
    Search and filter criteria for InterviewQuestion queries.
    """
    # Char Filters
    question = django_filters.CharFilter(field_name='question', lookup_expr='icontains', label='Search Question Text')
    short_description = django_filters.CharFilter(field_name='short_description', lookup_expr='icontains', label='Search Short Description')
    
    # ForeignKey relation ID filters
    category = django_filters.NumberFilter(field_name='category_id', label='Category ID')
    topic = django_filters.NumberFilter(field_name='topic_id', label='Topic ID')
    company = django_filters.NumberFilter(field_name='company_id', label='Company ID')
    role = django_filters.NumberFilter(field_name='role_id', label='Job Role ID')
    
    difficulty = django_filters.CharFilter(field_name='difficulty', lookup_expr='iexact', label='Difficulty')
    answer_type = django_filters.CharFilter(field_name='answer_type', lookup_expr='iexact', label='Answer Type')
    source = django_filters.CharFilter(field_name='source', lookup_expr='iexact', label='Source')
    
    # Date bounds
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label='Created after')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label='Created before')

    class Meta:
        model = InterviewQuestion
        fields = ['category', 'topic', 'company', 'role', 'difficulty', 'answer_type', 'source']
