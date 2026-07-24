from django.urls import path
from .views import (
    ResumeListView,
    ResumeUploadView,
    ResumeDetailView,
    ResumeDownloadView,
    ResumeSetDefaultView,
    ResumeTextView,
    ResumeVersionsView,
    ResumeActivityView,
    ResumeAnalysisView,
    ResumeJobMatchView
)

urlpatterns = [
    path('', ResumeListView.as_view(), name='resume_list'),
    path('upload', ResumeUploadView.as_view(), name='resume_upload'),
    path('analysis', ResumeAnalysisView.as_view(), name='resume_analysis'),
    path('match', ResumeJobMatchView.as_view(), name='resume_job_match'),
    path('<int:id>', ResumeDetailView.as_view(), name='resume_detail'),

    
    # Custom operations paths
    path('<int:id>/download', ResumeDownloadView.as_view(), name='resume_download'),
    path('<int:id>/default', ResumeSetDefaultView.as_view(), name='resume_set_default'),
    path('<int:id>/text', ResumeTextView.as_view(), name='resume_text'),
    path('<int:id>/versions', ResumeVersionsView.as_view(), name='resume_versions'),
    path('<int:id>/activity', ResumeActivityView.as_view(), name='resume_activity'),
]
