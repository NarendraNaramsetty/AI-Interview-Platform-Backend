from django.urls import path
from .views import (
    UserProfileView,
    AvatarUploadView,
    UserStatisticsView,
    AchievementsView,
    LeaderboardView,
    SkillsView,
    SkillsDetailView,
    UserPreferenceView,
    DashboardSummaryView,
    PublicProfileView
)

urlpatterns = [
    path('profile', UserProfileView.as_view(), name='user_profile'),
    path('avatar', AvatarUploadView.as_view(), name='user_avatar_upload'),
    path('statistics', UserStatisticsView.as_view(), name='user_statistics'),
    path('achievements', AchievementsView.as_view(), name='user_achievements'),
    path('leaderboard', LeaderboardView.as_view(), name='user_leaderboard'),
    
    # Skills list and sub-resources
    path('skills', SkillsView.as_view(), name='user_skills'),
    path('skills/<int:id>', SkillsDetailView.as_view(), name='user_skills_detail'),
    
    path('preferences', UserPreferenceView.as_view(), name='user_preferences'),
    path('dashboard-summary', DashboardSummaryView.as_view(), name='user_dashboard_summary'),
    
    # Public profile lookup (Must be last pattern to prevent shadowing specific paths)
    path('<str:username>', PublicProfileView.as_view(), name='public_profile'),
]
