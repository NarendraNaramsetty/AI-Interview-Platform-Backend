import django_filters
from .models import InterviewEvaluation

class InterviewEvaluationFilter(django_filters.FilterSet):
    """
    Filter set to query and slice evaluations list.
    Supports filtering by status, rating, min/max score boundaries, and evaluation date ranges.
    """
    status = django_filters.CharFilter(field_name='evaluation_status')
    rating = django_filters.CharFilter(field_name='overall_evaluation__overall_rating')
    
    min_score = django_filters.NumberFilter(field_name='overall_evaluation__overall_score', lookup_expr='gte')
    max_score = django_filters.NumberFilter(field_name='overall_evaluation__overall_score', lookup_expr='lte')
    
    start_date = django_filters.DateTimeFilter(field_name='evaluated_at', lookup_expr='gte')
    end_date = django_filters.DateTimeFilter(field_name='evaluated_at', lookup_expr='lte')

    class Meta:
        model = InterviewEvaluation
        fields = ['status', 'rating', 'min_score', 'max_score', 'start_date', 'end_date']
