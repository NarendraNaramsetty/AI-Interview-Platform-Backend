from django.contrib import admin
from .models import (
    ChatSession,
    ChatMessage,
    PromptTemplate,
    ChatFeedback,
    ChatBookmark,
    ChatHistory
)

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    fields = ['sender', 'message', 'message_type', 'token_count', 'processing_time', 'created_at']
    readonly_fields = ['created_at']


class ChatHistoryInline(admin.TabularInline):
    model = ChatHistory
    extra = 0
    fields = ['action', 'description', 'timestamp']
    readonly_fields = ['timestamp']


class ChatFeedbackInline(admin.StackedInline):
    model = ChatFeedback
    extra = 0
    fields = ['rating', 'comment', 'created_at']
    readonly_fields = ['created_at']


class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'uuid', 'user', 'title', 'conversation_type', 'status', 'total_messages', 'started_at', 'last_activity']
    list_filter = ['conversation_type', 'status', 'started_at', 'last_activity']
    search_fields = ['title', 'user__email', 'user__first_name', 'user__last_name']
    inlines = [ChatMessageInline, ChatHistoryInline]
    ordering = ['-last_activity']


class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'sender', 'message_type', 'token_count', 'processing_time', 'created_at']
    list_filter = ['sender', 'message_type', 'created_at']
    search_fields = ['message', 'session__title', 'session__user__email']
    inlines = [ChatFeedbackInline]
    ordering = ['created_at']


admin.site.register(ChatSession, ChatSessionAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(PromptTemplate)
admin.site.register(ChatFeedback)
admin.site.register(ChatBookmark)
admin.site.register(ChatHistory)
