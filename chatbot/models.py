import uuid
from django.db import models
from django.conf import settings
from .validators import validate_rating, validate_message_length

class Category(models.Model):
    """
    Categorization details for knowledge base questions.
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class ChatSession(models.Model):
    """
    Groups conversational message streams.
    """
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    session_title = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Chat Session"
        verbose_name_plural = "Chat Sessions"

    @property
    def title(self):
        return self.session_title

    @title.setter
    def title(self, value):
        self.session_title = value

    @property
    def status(self):
        return "Active" if self.is_active else "Deleted"

    def __str__(self):
        return f"{self.session_title} - Active: {self.is_active}"


class ChatMessage(models.Model):
    """
    Individual conversational message bubbles.
    """
    SENDER_CHOICES = [
        ('USER', 'USER'),
        ('BOT', 'BOT'),
    ]

    SOURCE_CHOICES = [
        ('LOCAL', 'LOCAL'),
        ('GEMINI', 'GEMINI'),
        ('GROK', 'GROK'),
        ('OLLAMA', 'OLLAMA'),
    ]

    id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.CharField(
        max_length=10,
        choices=SENDER_CHOICES,
        default='USER'
    )
    message = models.TextField(validators=[validate_message_length])
    response_source = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        null=True,
        blank=True
    )
    confidence_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        return f"Msg {self.id} by {self.sender} in Session {self.session_id}"


class KnowledgeBase(models.Model):
    """
    Local knowledge base entries containing Q&A pairs.
    """
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='knowledge_entries'
    )
    question = models.TextField()
    answer = models.TextField()
    keywords = models.TextField(help_text="Comma-separated keywords")
    synonyms = models.TextField(help_text="Comma-separated synonyms", blank=True)
    priority = models.IntegerField(default=0)
    difficulty = models.CharField(max_length=50, default="Medium")
    tags = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-created_at']
        verbose_name = "Knowledge Base Entry"
        verbose_name_plural = "Knowledge Base Entries"

    def __str__(self):
        return f"{self.title} ({self.category.name})"


class Feedback(models.Model):
    """
    Quality control user feedback containing ratings and comments.
    """
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_feedbacks'
    )
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    rating = models.IntegerField(validators=[validate_rating])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Chat Feedback"
        verbose_name_plural = "Chat Feedbacks"

    def __str__(self):
        return f"Feedback: Msg {self.message_id} -> Rating: {self.rating}"


class AdminAnalytics(models.Model):
    """
    Database analytics logs for failed queries, AI fallbacks, and overall usage tracking.
    """
    id = models.BigAutoField(primary_key=True)
    query = models.TextField()
    matched_knowledge = models.ForeignKey(
        KnowledgeBase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_hits'
    )
    was_matched = models.BooleanField(default=False)
    confidence_score = models.FloatField(default=0.0)
    response_source = models.CharField(max_length=15, default='GEMINI')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Admin Analytics Record"
        verbose_name_plural = "Admin Analytics Records"

    def __str__(self):
        return f"Query: '{self.query[:30]}' Matched: {self.was_matched} Source: {self.response_source}"
