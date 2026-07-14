from rest_framework import serializers
from .models import Category, ChatSession, ChatMessage, KnowledgeBase, Feedback, AdminAnalytics
from .validators import validate_rating, validate_message_length

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class CreateSessionRequestSerializer(serializers.Serializer):
    session_title = serializers.CharField(max_length=255, required=False, allow_blank=True)


class SendMessageRequestSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(required=True)
    message = serializers.CharField(required=True, validators=[validate_message_length])


class ChatFeedbackRequestSerializer(serializers.Serializer):
    message_id = serializers.IntegerField(required=True)
    rating = serializers.IntegerField(validators=[validate_rating])
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'session_title', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'is_active', 'created_at', 'updated_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'sender', 'message', 'response_source', 'confidence_score', 'created_at']
        read_only_fields = ['id', 'session', 'sender', 'response_source', 'confidence_score', 'created_at']


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)

    class Meta:
        model = KnowledgeBase
        fields = [
            'id', 'title', 'category', 'category_detail', 'question', 'answer', 
            'keywords', 'synonyms', 'priority', 'difficulty', 'tags', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'user', 'message', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class AdminAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminAnalytics
        fields = '__all__'
