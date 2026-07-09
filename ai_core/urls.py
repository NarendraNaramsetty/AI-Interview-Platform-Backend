from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AIProviderViewSet,
    AIModelViewSet,
    AIHealthCheckView,
    AIConfigurationView,
    AIUsageStatisticsView,
    AIRequestLogListView
)

router = DefaultRouter(trailing_slash=False)
router.register('providers', AIProviderViewSet, basename='ai-provider')
router.register('models', AIModelViewSet, basename='ai-model')

urlpatterns = [
    re_path(r'^health/?$', AIHealthCheckView.as_view(), name='ai_health_check'),
    re_path(r'^config/?$', AIConfigurationView.as_view(), name='ai_config'),
    re_path(r'^statistics/?$', AIUsageStatisticsView.as_view(), name='ai_statistics'),
    re_path(r'^logs/?$', AIRequestLogListView.as_view(), name='ai_logs_list'),

    # Router urls for providers and models
    path('', include(router.urls)),
]
