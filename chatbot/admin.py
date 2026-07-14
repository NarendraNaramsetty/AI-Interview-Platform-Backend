from django.contrib import admin
from .models import Category, ChatSession, ChatMessage, KnowledgeBase, Feedback, AdminAnalytics

@admin.action(description="Mark selected knowledge base entries as active")
def make_active(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description="Mark selected knowledge base entries as inactive")
def make_inactive(modeladmin, request, queryset):
    queryset.update(is_active=False)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'category', 'priority', 'difficulty', 'is_active', 'created_at', 'updated_at']
    list_filter = ['category', 'difficulty', 'is_active', 'created_at']
    search_fields = ['title', 'question', 'answer', 'keywords', 'synonyms', 'tags']
    actions = [make_active, make_inactive]
    ordering = ['-priority', '-created_at']


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    fields = ['sender', 'message', 'response_source', 'confidence_score', 'created_at']
    readonly_fields = ['created_at']


class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_title', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['session_title', 'user__email', 'user__first_name', 'user__last_name']
    inlines = [ChatMessageInline]
    ordering = ['-updated_at']


class ChatFeedbackInline(admin.StackedInline):
    model = Feedback
    extra = 0
    fields = ['user', 'rating', 'comment', 'created_at']
    readonly_fields = ['created_at']


class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'sender', 'response_source', 'confidence_score', 'created_at']
    list_filter = ['sender', 'response_source', 'created_at']
    search_fields = ['message', 'session__session_title', 'session__user__email']
    inlines = [ChatFeedbackInline]
    ordering = ['created_at']


class ChatFeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'message', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['comment', 'user__email', 'message__message']
    ordering = ['-created_at']


class AdminAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['id', 'query', 'was_matched', 'confidence_score', 'response_source', 'created_at']
    list_filter = ['was_matched', 'response_source', 'created_at']
    search_fields = ['query', 'matched_knowledge__title']
    ordering = ['-created_at']


admin.site.register(Category, CategoryAdmin)
admin.site.register(KnowledgeBase, KnowledgeBaseAdmin)
admin.site.register(ChatSession, ChatSessionAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(Feedback, ChatFeedbackAdmin)
admin.site.register(AdminAnalytics, AdminAnalyticsAdmin)
