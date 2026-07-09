import django_filters
from django.db.models import Q
from .models import UserProfile

class UserProfileFilter(django_filters.FilterSet):
    """
    Search and filter criteria for UserProfiles.
    Supports lookups by user email (username), company, roles, and skills.
    """
    username = django_filters.CharFilter(method='filter_username', label='Search by name or email')
    skills = django_filters.CharFilter(method='filter_skills', label='Search by comma-separated skills')
    company = django_filters.CharFilter(field_name='preferred_company', lookup_expr='icontains', label='Preferred Company')
    role = django_filters.CharFilter(field_name='preferred_job_role', lookup_expr='icontains', label='Preferred Role')

    class Meta:
        model = UserProfile
        fields = ['preferred_interview_language', 'experience_level', 'location']

    def filter_username(self, queryset, name, value):
        """
        Filters queryset matching first name, last name, or email.
        """
        if not value:
            return queryset
        return queryset.filter(
            Q(user__email__icontains=value) | 
            Q(user__first_name__icontains=value) | 
            Q(user__last_name__icontains=value)
        )

    def filter_skills(self, queryset, name, value):
        """
        Filters users possessing all the specified skills (case-insensitive).
        Format: ?skills=Python,SQL
        """
        if not value:
            return queryset
        
        skills_list = [s.strip().lower() for s in value.split(',') if s.strip()]
        for skill in skills_list:
            queryset = queryset.filter(skills__icontains=skill)
            
        return queryset
