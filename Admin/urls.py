from django.urls import path
from .views import (
    AdminLoginView,
    AdminTokenRefreshView,
    AdminDashboardView,
    AdminUserListView,
    AdminUserDetailView,
    AdminPaymentsView,
    AdminInterviewsView,
    AdminQuestionsView,
    AdminQuestionsBulkUploadView,
    AdminNotificationsView,
    AdminSupportInboxView,
    AdminLogsView,
    AdminSettingsView,
    AdminSystemView,
    AdminDatabaseView,
    AdminSidebarMenuView
)

urlpatterns = [
    path('login/', AdminLoginView.as_view(), name='admin_login'),
    path('token/refresh/', AdminTokenRefreshView.as_view(), name='admin_token_refresh'),
    path('dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    
    path('users/', AdminUserListView.as_view(), name='admin_users_list_api'),
    path('users/<int:id>/', AdminUserDetailView.as_view(), name='admin_user_detail_api'),
    
    path('payments/', AdminPaymentsView.as_view(), name='admin_payments'),
    path('interviews/', AdminInterviewsView.as_view(), name='admin_interviews'),
    
    path('questions/', AdminQuestionsView.as_view(), name='admin_questions'),
    path('questions/upload/', AdminQuestionsBulkUploadView.as_view(), name='admin_questions_upload'),
    
    path('notification/', AdminNotificationsView.as_view(), name='admin_notifications'),
    path('support/', AdminSupportInboxView.as_view(), name='admin_support'),
    path('logs/', AdminLogsView.as_view(), name='admin_logs'),
    path('settings/', AdminSettingsView.as_view(), name='admin_settings'),
    path('system/', AdminSystemView.as_view(), name='admin_system'),
    path('database/', AdminDatabaseView.as_view(), name='admin_database'),
    path('sidebar-menu/', AdminSidebarMenuView.as_view(), name='admin_sidebar_menu'),
]
