import django_filters
from .models import ChatSession, PromptTemplate

class ChatSessionFilter(django_filters.FilterSet):
    """
    Filters chat sessions list by type (General, Resume, etc), status (Active, Archived), or created dates.
    """
    type = django_filters.CharFilter(field_name='conversation_type')
    status = django_filters.CharFilter(field_name='status')
    
    start_date = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    end_date = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = ChatSession
        fields = ['type', 'status', 'start_date', 'end_date']


class PromptTemplateFilter(django_filters.FilterSet):
    """
    Filters prompt templates by category and active statuses.
    """
    category = django_filters.CharFilter(field_name='category')
    is_active = django_filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = PromptTemplate
        fields = ['category', 'is_active']
