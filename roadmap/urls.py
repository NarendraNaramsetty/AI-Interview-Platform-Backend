from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CareerPathListView,
    RoadmapViewSet,
    StartRoadmapView,
    UpdateProgressView,
    PauseRoadmapView,
    ResumeRoadmapView,
    CurrentRoadmapView,
    CompletedRoadmapsListView,
    LearningResourceListView,
    LearningStatisticsView,
    LearningReminderViewSet
)

router = DefaultRouter(trailing_slash=False)
router.register('reminders', LearningReminderViewSet, basename='roadmap-reminder')
router.register('', RoadmapViewSet, basename='roadmap-item')

urlpatterns = [
    re_path(r'^careers/?$', CareerPathListView.as_view(), name='roadmap_careers'),
    re_path(r'^start/?$', StartRoadmapView.as_view(), name='roadmap_start'),
    re_path(r'^progress/?$', UpdateProgressView.as_view(), name='roadmap_progress'),
    re_path(r'^current/?$', CurrentRoadmapView.as_view(), name='roadmap_current'),
    re_path(r'^completed/?$', CompletedRoadmapsListView.as_view(), name='roadmap_completed'),
    re_path(r'^pause/?$', PauseRoadmapView.as_view(), name='roadmap_pause'),
    re_path(r'^resume/?$', ResumeRoadmapView.as_view(), name='roadmap_resume'),
    re_path(r'^resources/?$', LearningResourceListView.as_view(), name='roadmap_resources'),
    re_path(r'^statistics/?$', LearningStatisticsView.as_view(), name='roadmap_statistics'),
    
    # Router configurations
    path('', include(router.urls)),
]
