"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# pyrefly: ignore [missing-import]
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)

urlpatterns = [
    # Django Admin Portal
    path('admin/', admin.site.urls),

    # Authentication Module APIs
    path('api/auth/', include('accounts.urls')),

    # Users Module APIs
    path('api/users/', include('users.urls')),

    # Resume Module APIs
    path('api/resume/', include('resume.urls')),

    # Interview Module APIs
    path('api/interviews/', include('interviews.urls')),

    # Question Bank Module APIs
    path('api/questions/', include('questions.urls')),

    # Feedback & AI Evaluation Module APIs
    path('api/feedback/', include('feedback.urls')),

    # Coding Module APIs
    path('api/coding/', include('coding.urls')),

    # Learning Roadmap Module APIs
    path('api/roadmap/', include('roadmap.urls')),

    # AI Chatbot Module APIs
    path('api/chatbot/', include('chatbot.urls')),

    # Admin Module APIs
    path('api/admin/', include('Admin.urls')),

    # Dashboard Module APIs
    path('api/dashboard/', include('Dashboard.urls')),

    # Notifications Module APIs
    path('api/notifications/', include('Notifications.urls')),

    # Payments Module APIs
    path('api/payments/', include('Payments.urls')),

    # AI Core Module APIs
    path('api/ai/', include('ai_core.urls')),

    # drf-spectacular documentation API endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serving avatar media files during local development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
