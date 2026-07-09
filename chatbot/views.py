from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from django_filters.rest_framework import DjangoFilterBackend
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from .models import (
    ChatSession,
    ChatMessage,
    PromptTemplate,
    ChatFeedback,
    ChatBookmark,
    ChatHistory
)
from .permissions import IsOwnerOrAdmin, IsAdminOrReadOnly
from .filters import ChatSessionFilter, PromptTemplateFilter
from .services import ChatbotService
from .pagination import PrepAIPagination
from .serializers import (
    StartChatSessionRequestSerializer,
    SendMessageRequestSerializer,
    RenameChatSessionRequestSerializer,
    PromptTemplateSerializer,
    ChatFeedbackSerializer,
    ChatBookmarkSerializer,
    ChatHistorySerializer,
    ChatMessageSerializer,
    ChatSessionSerializer
)
from .constants import STATUS_ACTIVE, STATUS_DELETED, STATUS_ARCHIVED

class StartChatSessionView(APIView):
    """
    POST /api/chatbot/session/start
    Start session. Logs conversation start history event.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Start Chat Session",
        request=StartChatSessionRequestSerializer,
        responses={201: ChatSessionSerializer}
    )
    def post(self, request):
        serializer = StartChatSessionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conv_type = serializer.validated_data['conversation_type']

        session = ChatbotService.start_chat_session(conv_type, request.user)
        response_serializer = ChatSessionSerializer(session)
        return Response({
            "success": True,
            "message": "Chat session started successfully.",
            "data": response_serializer.data
        }, status=status.HTTP_201_CREATED)


class CurrentChatSessionView(APIView):
    """
    GET /api/chatbot/session/current
    Returns currently active chat session.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Current Active Chat Session",
        responses={200: ChatSessionSerializer}
    )
    def get(self, request):
        session = ChatSession.objects.filter(
            user=request.user,
            status=STATUS_ACTIVE
        ).first()

        if not session:
            return Response({
                "success": True,
                "message": "No active chat session found.",
                "data": None
            }, status=status.HTTP_200_OK)

        serializer = ChatSessionSerializer(session)
        return Response({
            "success": True,
            "message": "Current active session retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class ChatSessionViewSet(viewsets.ModelViewSet):
    """
    GET /api/chatbot/sessions
    PUT /api/chatbot/session/{id}
    POST /api/chatbot/session/{id}/archive
    DELETE /api/chatbot/session/{id} (Soft delete)
    """
    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ChatSessionFilter
    ordering_fields = ['last_activity', 'created_at']
    ordering = ['-last_activity']
    search_fields = ['title']
    pagination_class = PrepAIPagination
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        queryset = ChatSession.objects.filter(user=user)
        # Admins can see soft-deleted ones if needed, standard candidates exclude them.
        if user.is_staff:
            return ChatSession.objects.all()
        return queryset.exclude(status=STATUS_DELETED)

    def update(self, request, *args, **kwargs):
        # Allow PUT / PATCH requests to rename session title
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = RenameChatSessionRequestSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "success": True,
            "message": "Session renamed successfully.",
            "data": ChatSessionSerializer(instance).data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        # Soft delete session
        instance = self.get_object()
        ChatbotService.delete_session(instance.id, request.user)
        return Response({
            "success": True,
            "message": "Session deleted successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='archive')
    def archive(self, request, id=None):
        # Archive session action
        instance = self.get_object()
        ChatbotService.archive_session(instance.id, request.user)
        return Response({
            "success": True,
            "message": "Session archived successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)


class SendMessageView(APIView):
    """
    POST /api/chatbot/message
    Sends user message and returns mock AI placeholder.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Send User Message to Chatbot",
        request=SendMessageRequestSerializer,
        responses={201: ChatMessageSerializer}
    )
    def post(self, request):
        serializer = SendMessageRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.validated_data['session_id']
        message = serializer.validated_data['message']

        try:
            ai_msg = ChatbotService.send_message(session_id, message, request.user)
            response_serializer = ChatMessageSerializer(ai_msg, context={'request': request})
            return Response({
                "success": True,
                "message": "Message sent successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_201_CREATED)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class ChatMessagesListView(generics.ListAPIView):
    """
    GET /api/chatbot/messages/{session_id}
    Retrieves all messages for a specific session.
    """
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    pagination_class = None

    def get_queryset(self):
        session_id = self.kwargs['session_id']
        # Ownership check is done by calling get_object on the session or checking permission
        session = get_object_or_404(ChatSession, pk=session_id)
        self.check_object_permissions(self.request, session)
        return ChatMessage.objects.filter(session=session).prefetch_related('bookmarks', 'feedback')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Messages retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class PromptTemplateViewSet(viewsets.ModelViewSet):
    """
    GET /api/chatbot/prompts
    GET /api/chatbot/prompts/{id}
    """
    queryset = PromptTemplate.objects.filter(is_active=True)
    serializer_class = PromptTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = PromptTemplateFilter
    search_fields = ['name', 'category', 'description']
    pagination_class = PrepAIPagination
    lookup_field = 'id'

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Prompt templates retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class ChatFeedbackView(APIView):
    """
    POST /api/chatbot/feedback
    Submit rating feed for specific AI message bubble.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Submit Message Rating Feedback",
        request=ChatFeedbackSerializer,
        responses={201: ChatFeedbackSerializer}
    )
    def post(self, request):
        serializer = ChatFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verify ownership of message before rating feedback
        msg = get_object_or_404(ChatMessage, pk=serializer.validated_data['chat_message'].id)
        if msg.session.user != request.user:
            return Response({
                "success": False,
                "message": "Permission Error",
                "errors": {"detail": "You do not own the conversation for this message."}
            }, status=status.HTTP_403_FORBIDDEN)

        serializer.save()
        return Response({
            "success": True,
            "message": "Feedback submitted successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class ChatBookmarkViewSet(viewsets.ModelViewSet):
    """
    GET /api/chatbot/bookmarks
    POST /api/chatbot/bookmarks
    DELETE /api/chatbot/bookmarks/{id}
    """
    serializer_class = ChatBookmarkSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    pagination_class = None
    lookup_field = 'id'

    def get_queryset(self):
        return ChatBookmark.objects.filter(user=self.request.user).select_related('chat_message')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Bookmarks retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validate that user owns the message they are bookmarking
        msg = get_object_or_404(ChatMessage, pk=serializer.validated_data['chat_message'].id)
        if msg.session.user != request.user:
            return Response({
                "success": False,
                "message": "Permission Error",
                "errors": {"detail": "You do not own this chat session."}
            }, status=status.HTTP_403_FORBIDDEN)

        # Unique bookmark constraint
        existing = ChatBookmark.objects.filter(user=request.user, chat_message=msg).first()
        if existing:
            return Response({
                "success": True,
                "message": "Message is already bookmarked.",
                "data": ChatBookmarkSerializer(existing).data
            }, status=status.HTTP_200_OK)

        self.perform_create(serializer)
        return Response({
            "success": True,
            "message": "Message bookmarked successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "success": True,
            "message": "Bookmark removed successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)


class ChatHistoryListView(generics.ListAPIView):
    """
    GET /api/chatbot/history/{session_id}
    Retrieves history logs of a specific chat session.
    """
    serializer_class = ChatHistorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    pagination_class = None

    def get_queryset(self):
        session_id = self.kwargs['session_id']
        session = get_object_or_404(ChatSession, pk=session_id)
        self.check_object_permissions(self.request, session)
        return ChatHistory.objects.filter(session=session)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Session history retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
