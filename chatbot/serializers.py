from rest_framework import serializers
from .models import (
    ChatSession,
    ChatMessage,
    PromptTemplate,
    ChatFeedback,
    ChatBookmark,
    ChatHistory
)
from .validators import validate_rating, validate_message_length
from .constants import CONVERSATION_TYPE_CHOICES, CONV_GENERAL

# ----------------------------------------------------
# Request Payload Serializers
# ----------------------------------------------------

class StartChatSessionRequestSerializer(serializers.Serializer):
    conversation_type = serializers.ChoiceField(
        choices=CONVERSATION_TYPE_CHOICES,
        default=CONV_GENERAL
    )


class SendMessageRequestSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(required=True)
    message = serializers.CharField(required=True, validators=[validate_message_length])


class RenameChatSessionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['title']


# ----------------------------------------------------
# Model Representation Serializers
# ----------------------------------------------------

class PromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptTemplate
        fields = ['id', 'uuid', 'name', 'category', 'description', 'system_prompt', 'is_active']
        read_only_fields = ['id', 'uuid']


class ChatFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatFeedback
        fields = ['id', 'chat_message', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatBookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatBookmark
        fields = ['id', 'uuid', 'user', 'chat_message', 'created_at']
        read_only_fields = ['id', 'uuid', 'user', 'created_at']


class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ['id', 'session', 'action', 'description', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class ChatMessageSerializer(serializers.ModelSerializer):
    feedback = ChatFeedbackSerializer(read_only=True)
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ['id', 'uuid', 'session', 'sender', 'message', 'message_type', 'token_count', 'processing_time', 'feedback', 'is_bookmarked', 'created_at']
        read_only_fields = ['id', 'uuid', 'sender', 'message_type', 'token_count', 'processing_time', 'created_at']

    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.bookmarks.filter(user=request.user).exists()
        return False


class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['id', 'uuid', 'user', 'title', 'conversation_type', 'status', 'total_messages', 'started_at', 'last_activity', 'created_at', 'updated_at']
        read_only_fields = ['id', 'uuid', 'user', 'total_messages', 'status', 'started_at', 'last_activity', 'created_at', 'updated_at']
