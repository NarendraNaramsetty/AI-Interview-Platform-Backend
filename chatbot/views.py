from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db.models import Count
from rest_framework import permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Category, ChatSession, ChatMessage, KnowledgeBase, Feedback, AdminAnalytics
from .serializers import (
    CreateSessionRequestSerializer,
    SendMessageRequestSerializer,
    ChatFeedbackRequestSerializer,
    ChatSessionSerializer,
    ChatMessageSerializer,
    KnowledgeBaseSerializer,
    ChatFeedbackSerializer,
    CategorySerializer
)
from .services import ChatbotService, get_chat_history, store_feedback

class SendMessageView(APIView):
    """
    POST /api/chat/
    Send user message, search local DB, fallback to Gemini, and return response.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SendMessageRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_id = serializer.validated_data['session_id']
        message = serializer.validated_data['message']

        try:
            # Business logic completely in services.py
            ai_msg = ChatbotService.send_message(session_id, message, request.user)
            response_serializer = ChatMessageSerializer(ai_msg)
            return Response({
                "success": True,
                "message": "Response generated successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ChatHistoryListView(APIView):
    """
    GET /api/chat/history/
    Retrieves all messages for a specific session via ?session_id=<id>
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({
                "success": False,
                "message": "Missing 'session_id' query parameter."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            session_id = int(session_id)
        except ValueError:
            return Response({
                "success": False,
                "message": "Invalid 'session_id' parameter."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Confirm ownership of session
        session = get_object_or_404(ChatSession, pk=session_id, user=request.user)
        
        # Call service layer logic
        history = get_chat_history(session.id, request.user)
        serializer = ChatMessageSerializer(history, many=True)
        return Response({
            "success": True,
            "message": "Chat history retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class ChatSessionListView(APIView):
    """
    GET /api/chat/sessions/
    Lists all active sessions for the user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user, is_active=True).order_by('-updated_at')
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response({
            "success": True,
            "message": "Sessions retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class CreateSessionView(APIView):
    """
    POST /api/chat/session/
    Creates a new chat session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateSessionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_title = serializer.validated_data.get('session_title')
        # Call service layer logic
        session = ChatbotService.start_chat_session(session_title, request.user)
        response_serializer = ChatSessionSerializer(session)
        
        return Response({
            "success": True,
            "message": "Session created successfully.",
            "data": response_serializer.data
        }, status=status.HTTP_201_CREATED)


class DeleteSessionView(APIView):
    """
    DELETE /api/chat/session/<id>/
    Soft deletes (deactivates) a session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, id):
        try:
            # Business logic completely in services.py
            ChatbotService.delete_session(id, request.user)
            return Response({
                "success": True,
                "message": "Session deleted successfully."
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ChatFeedbackView(APIView):
    """
    POST /api/chat/feedback/
    Stores feedback rating and comment.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatFeedbackRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        msg_id = serializer.validated_data['message_id']
        rating = serializer.validated_data['rating']
        comment = serializer.validated_data.get('comment', '')

        # Confirm user owns the message session
        msg = get_object_or_404(ChatMessage, pk=msg_id)
        if msg.session.user != request.user:
            return Response({
                "success": False,
                "message": "You cannot submit feedback for this conversation message."
            }, status=status.HTTP_403_FORBIDDEN)

        # Call service layer logic
        feedback = store_feedback(request.user, msg.id, rating, comment)
        response_serializer = ChatFeedbackSerializer(feedback)
        
        return Response({
            "success": True,
            "message": "Feedback submitted successfully.",
            "data": response_serializer.data
        }, status=status.HTTP_201_CREATED)


class CategoryListView(APIView):
    """
    GET /api/chat/categories/
    Lists all available chatbot question categories.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response({
            "success": True,
            "message": "Categories retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """
    GET /api/chat/knowledge/
    POST /api/chat/knowledge/
    PUT /api/chat/knowledge/<id>/
    DELETE /api/chat/knowledge/<id>/
    Admin API for CRUD over KnowledgeBase.
    """
    queryset = KnowledgeBase.objects.all().select_related('category')
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    lookup_field = 'id'

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Knowledge entries retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "success": True,
            "message": "Knowledge entry created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "success": True,
            "message": "Knowledge entry updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "success": True,
            "message": "Knowledge entry deleted successfully."
        }, status=status.HTTP_200_OK)


class AdminCategoryViewSet(viewsets.ModelViewSet):
    """
    Admin CRUD ViewSet for category management.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    lookup_field = 'id'


class ChatbotAdminAnalyticsView(APIView):
    """
    GET /api/chat/analytics/
    Calculates dynamic chatbot usage analytics directly from Neon PostgreSQL using Django aggregates.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get(self, request):
        total_queries = AdminAnalytics.objects.count()
        matched_queries = AdminAnalytics.objects.filter(was_matched=True).count()
        failed_queries = AdminAnalytics.objects.filter(was_matched=False).count()
        
        # Calculate rates
        match_rate = round((matched_queries / total_queries * 100.0), 2) if total_queries > 0 else 0.0
        
        # Top matched questions
        top_questions = (
            AdminAnalytics.objects.filter(was_matched=True)
            .values('matched_knowledge__title', 'matched_knowledge__question')
            .annotate(hits=Count('id'))
            .order_by('-hits')[:5]
        )

        # Top search categories
        top_categories = (
            AdminAnalytics.objects.filter(was_matched=True)
            .values('matched_knowledge__category__name')
            .annotate(hits=Count('id'))
            .order_by('-hits')[:5]
        )

        # Common failed search phrases
        failed_searches = (
            AdminAnalytics.objects.filter(was_matched=False)
            .values('query')
            .annotate(hits=Count('id'))
            .order_by('-hits')[:10]
        )

        # AI Usage breakdown
        ai_usage = (
            AdminAnalytics.objects.filter(was_matched=False)
            .values('response_source')
            .annotate(usage_count=Count('id'))
            .order_by('-usage_count')
        )

        return Response({
            "success": True,
            "message": "Admin chatbot analytics calculated successfully.",
            "data": {
                "summary": {
                    "total_queries": total_queries,
                    "matched_queries": matched_queries,
                    "failed_queries": failed_queries,
                    "match_rate_percentage": match_rate
                },
                "top_questions": list(top_questions),
                "top_categories": list(top_categories),
                "failed_searches": list(failed_searches),
                "ai_usage": list(ai_usage)
            }
        }, status=status.HTTP_200_OK)
