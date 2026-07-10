from django.urls import path
from .ai_views import GenerateAIQuestionView, ReviewAICodeView, CodingLearningDashboardView

urlpatterns = [
    path('generate-question/', GenerateAIQuestionView.as_view(), name='ai-generate-question'),
    path('review-code/', ReviewAICodeView.as_view(), name='ai-review-code'),
    path('coding-dashboard/', CodingLearningDashboardView.as_view(), name='ai-coding-dashboard'),
]
