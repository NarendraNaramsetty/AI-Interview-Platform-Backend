from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StartChatSessionView,
    CurrentChatSessionView,
    ChatSessionViewSet,
    SendMessageView,
    ChatMessagesListView,
    PromptTemplateViewSet,
    ChatFeedbackView,
    ChatBookmarkViewSet,
    ChatHistoryListView
)

router = DefaultRouter(trailing_slash=False)
router.register('prompts', PromptTemplateViewSet, basename='chatbot-prompt')
router.register('bookmarks', ChatBookmarkViewSet, basename='chatbot-bookmark')
router.register('session', ChatSessionViewSet, basename='chatbot-session')

urlpatterns = [
    re_path(r'^session/start/?$', StartChatSessionView.as_view(), name='chatbot_start_session'),
    re_path(r'^session/current/?$', CurrentChatSessionView.as_view(), name='chatbot_current_session'),
    re_path(r'^sessions/?$', ChatSessionViewSet.as_view({'get': 'list'}), name='chatbot_sessions_list'),
    re_path(r'^message/?$', SendMessageView.as_view(), name='chatbot_send_message'),
    re_path(r'^messages/(?P<session_id>\d+)/?$', ChatMessagesListView.as_view(), name='chatbot_messages_list'),
    re_path(r'^feedback/?$', ChatFeedbackView.as_view(), name='chatbot_feedback'),
    re_path(r'^history/(?P<session_id>\d+)/?$', ChatHistoryListView.as_view(), name='chatbot_history_list'),
    
    # Router configurations
    path('', include(router.urls)),
]
