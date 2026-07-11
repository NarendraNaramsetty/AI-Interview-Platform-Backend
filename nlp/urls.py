from django.urls import path
from .views import (
    NLPAnalysisView,
    InterviewSessionStartView,
    InterviewSessionAnswerView,
    CodingSandboxGenerateView,
    CodingChallengeSubmitView,
    CodingSandboxNextQuestionView,
    CoachChatStartView,
    CoachChatMessageView,
    CoachChatClearView,
    ResumeUploadAndAuditView,
    ResumeAuditDetailView
)

urlpatterns = [
    path("analyze", NLPAnalysisView.as_view(), name="nlp-analyze"),
    path("interview/start", InterviewSessionStartView.as_view(), name="nlp-interview-start"),
    path("interview/<int:session_id>/answer", InterviewSessionAnswerView.as_view(), name="nlp-interview-answer"),
    path("sandbox/generate", CodingSandboxGenerateView.as_view(), name="nlp-sandbox-generate"),
    path("sandbox/<int:id>/submit", CodingChallengeSubmitView.as_view(), name="nlp-sandbox-submit"),
    path("sandbox/<int:session_id>/next", CodingSandboxNextQuestionView.as_view(), name="nlp-sandbox-next"),
    path("coach/start", CoachChatStartView.as_view(), name="nlp-coach-start"),
    path("coach/<int:session_id>/message", CoachChatMessageView.as_view(), name="nlp-coach-message"),
    path("coach/<int:session_id>/clear", CoachChatClearView.as_view(), name="nlp-coach-clear"),
    path("resume/upload", ResumeUploadAndAuditView.as_view(), name="nlp-resume-upload"),
    path("resume/<int:audit_id>", ResumeAuditDetailView.as_view(), name="nlp-resume-detail"),
]
