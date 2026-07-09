from django.urls import re_path
from .views import DashboardStatsView, DashboardActivityView

urlpatterns = [
    re_path(r'^stats/?$', DashboardStatsView.as_view(), name='dashboard_stats'),
    re_path(r'^activity/?$', DashboardActivityView.as_view(), name='dashboard_activity'),
]
