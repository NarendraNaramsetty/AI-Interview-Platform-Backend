from django.urls import re_path
from .views import (
    InterviewEvaluationListView,
    GenerateEvaluationView,
    InterviewEvaluationDetailView,
    TechnicalEvaluationDetailView,
    CommunicationEvaluationDetailView,
    HRBehaviorEvaluationDetailView,
    OverallEvaluationDetailView,
    SuggestionsListView,
    SuggestionsDetailView,
    ResourcesListView,
    EvaluationHistoryListView,
    ExportReportView
)

urlpatterns = [
    re_path(r'^$', InterviewEvaluationListView.as_view(), name='evaluation_list'),
    re_path(r'^generate/?$', GenerateEvaluationView.as_view(), name='evaluation_generate'),
    re_path(r'^suggestions/(?P<id>\d+)/?$', SuggestionsDetailView.as_view(), name='suggestion_detail'),
    
    # Nested paths with interview_id variable capture
    re_path(r'^(?P<interview_id>\d+)/?$', InterviewEvaluationDetailView.as_view(), name='evaluation_detail'),
    re_path(r'^(?P<interview_id>\d+)/technical/?$', TechnicalEvaluationDetailView.as_view(), name='evaluation_technical'),
    re_path(r'^(?P<interview_id>\d+)/communication/?$', CommunicationEvaluationDetailView.as_view(), name='evaluation_communication'),
    re_path(r'^(?P<interview_id>\d+)/hr/?$', HRBehaviorEvaluationDetailView.as_view(), name='evaluation_hr'),
    re_path(r'^(?P<interview_id>\d+)/overall/?$', OverallEvaluationDetailView.as_view(), name='evaluation_overall'),
    re_path(r'^(?P<interview_id>\d+)/suggestions/?$', SuggestionsListView.as_view(), name='evaluation_suggestions_list'),
    re_path(r'^(?P<interview_id>\d+)/resources/?$', ResourcesListView.as_view(), name='evaluation_resources_list'),
    re_path(r'^(?P<interview_id>\d+)/history/?$', EvaluationHistoryListView.as_view(), name='evaluation_history_list'),
    re_path(r'^(?P<interview_id>\d+)/export/?$', ExportReportView.as_view(), name='evaluation_export'),
]
