from django.urls import re_path
from .views import (
    NotificationListView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
    NotificationSettingsView
)

urlpatterns = [
    re_path(r'^$', NotificationListView.as_view(), name='notifications_list'),
    re_path(r'^read-all/?$', MarkAllNotificationsReadView.as_view(), name='notifications_read_all'),
    re_path(r'^settings/?$', NotificationSettingsView.as_view(), name='notifications_settings'),
    re_path(r'^(?P<id>\d+)/read/?$', MarkNotificationReadView.as_view(), name='notifications_mark_read'),
]
