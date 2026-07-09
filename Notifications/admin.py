from django.contrib import admin
from .models import Notification, NotificationSetting

class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['is_read', 'notification_type', 'created_at']
    search_fields = ['user__email', 'title', 'message']


class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'email_enabled', 'push_enabled', 'frequency']
    list_filter = ['email_enabled', 'push_enabled', 'frequency']
    search_fields = ['user__email']


admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationSetting, NotificationSettingAdmin)
