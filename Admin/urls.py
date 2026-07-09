from django.urls import re_path
from .views import (
    AdminAnalyticsView,
    AdminUserListView,
    AdminUserDetailView,
    AdminExportUsersView,
    AdminExportInterviewsView
)

urlpatterns = [
    re_path(r'^analytics/?$', AdminAnalyticsView.as_view(), name='admin_analytics'),
    re_path(r'^users/?$', AdminUserListView.as_view(), name='admin_users_list'),
    re_path(r'^users/(?P<id>\d+)/?$', AdminUserDetailView.as_view(), name='admin_user_detail'),
    re_path(r'^exports/users/?$', AdminExportUsersView.as_view(), name='admin_export_users'),
    re_path(r'^exports/interviews/?$', AdminExportInterviewsView.as_view(), name='admin_export_interviews'),
]
