import django_filters
from .models import CodingProblem, CodeSubmission

class CodingProblemFilter(django_filters.FilterSet):
    """
    Filters coding challenges list by category, company, difficulty, or tag.
    """
    category = django_filters.NumberFilter(field_name='category_id')
    company = django_filters.NumberFilter(field_name='company_id')
    difficulty = django_filters.CharFilter(field_name='difficulty')
    tag = django_filters.CharFilter(field_name='tags', lookup_expr='icontains')

    class Meta:
        model = CodingProblem
        fields = ['category', 'company', 'difficulty', 'tag']


class CodeSubmissionFilter(django_filters.FilterSet):
    """
    Filters user previous submissions history by language, status, and timestamps.
    """
    language = django_filters.CharFilter(field_name='programming_language')
    status = django_filters.CharFilter(field_name='status')
    
    start_date = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    end_date = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = CodeSubmission
        fields = ['language', 'status', 'start_date', 'end_date']
