import uuid
from django.db import models
from django.conf import settings
from .constants import (
    CONVERSATION_TYPE_CHOICES,
    CONV_GENERAL,
    SESSION_STATUS_CHOICES,
    STATUS_ACTIVE,
    SENDER_CHOICES,
    SENDER_USER,
    MESSAGE_TYPE_CHOICES,
    MSG_TEXT
)
from .validators import validate_rating, validate_message_length

class ChatSession(models.Model):
    """
    Groups conversational message streams. Supports archiving and soft deletions.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    title = models.CharField(max_length=255)
    conversation_type = models.CharField(
        max_length=50,
        choices=CONVERSATION_TYPE_CHOICES,
        default=CONV_GENERAL
    )
    status = models.CharField(
        max_length=50,
        choices=SESSION_STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    total_messages = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_activity']
        verbose_name = "Chat Session"
        verbose_name_plural = "Chat Sessions"

    def __str__(self):
        return f"{self.title} ({self.conversation_type}) - Status: {self.status}"


class ChatMessage(models.Model):
    """
    Individual conversational message bubbles sent either by standard candidates or mock AI bots.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.CharField(
        max_length=50,
        choices=SENDER_CHOICES,
        default=SENDER_USER
    )
    message = models.TextField(validators=[validate_message_length])
    message_type = models.CharField(
        max_length=50,
        choices=MESSAGE_TYPE_CHOICES,
        default=MSG_TEXT
    )
    token_count = models.IntegerField(default=0)
    processing_time = models.FloatField(default=0.0)  # in seconds
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        return f"Msg {self.id} by {self.sender} in Session {self.session_id}"


class PromptTemplate(models.Model):
    """
    Pre-configured prompts injected inside LLM systems to establish agent behaviors.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=150, unique=True)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    system_prompt = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Prompt Template"
        verbose_name_plural = "Prompt Templates"

    def __str__(self):
        return self.name


class ChatFeedback(models.Model):
    """
    Quality control user feedback containing ratings and comments.
    """
    id = models.BigAutoField(primary_key=True)
    chat_message = models.OneToOneField(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    rating = models.IntegerField(validators=[validate_rating])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Chat Feedback"
        verbose_name_plural = "Chat Feedbacks"

    def __str__(self):
        return f"Feedback: Msg {self.chat_message_id} -> Rating: {self.rating}"


class ChatBookmark(models.Model):
    """
    Enables user bookmarks.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_bookmarks'
    )
    chat_message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'chat_message')
        ordering = ['-created_at']
        verbose_name = "Chat Bookmark"
        verbose_name_plural = "Chat Bookmarks"

    def __str__(self):
        return f"Bookmark: {self.user.email} -> Msg {self.chat_message_id}"


class ChatHistory(models.Model):
    """
    Timeline events logging session updates (Conversation Started, Message Sent, Conversation Archived).
    """
    id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='history_logs'
    )
    action = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Chat History"
        verbose_name_plural = "Chat Histories"

    def __str__(self):
        return f"{self.action} in Session {self.session_id} at {self.timestamp}"
