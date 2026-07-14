from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import (
    SendMessageView,
    ChatHistoryListView,
    ChatSessionListView,
    CreateSessionView,
    DeleteSessionView,
    ChatFeedbackView,
    CategoryListView,
    KnowledgeBaseViewSet,
    AdminCategoryViewSet,
    ChatbotAdminAnalyticsView
)

# Use SimpleRouter for clean Admin REST paths
router = SimpleRouter(trailing_slash=False)
router.register('knowledge', KnowledgeBaseViewSet, basename='chatbot-knowledge')
router.register('admin/categories', AdminCategoryViewSet, basename='chatbot-admin-categories')

urlpatterns = [
    # User Chat Operations
    path('', SendMessageView.as_view(), name='chat_send_message'),
    path('history/', ChatHistoryListView.as_view(), name='chat_history'),
    path('sessions/', ChatSessionListView.as_view(), name='chat_sessions'),
    
    # User Session Management
    path('session/', CreateSessionView.as_view(), name='chat_session_create'),
    path('session/<int:id>/', DeleteSessionView.as_view(), name='chat_session_delete'),
    
    # User Feedback & Info
    path('feedback/', ChatFeedbackView.as_view(), name='chat_feedback'),
    path('categories/', CategoryListView.as_view(), name='chat_categories'),
    
    # Admin Analytics Dashboard API
    path('analytics/', ChatbotAdminAnalyticsView.as_view(), name='chat_admin_analytics'),
    
    # Router Mount (Admin Knowledge & Categories REST CRUD)
    path('', include(router.urls)),
]
