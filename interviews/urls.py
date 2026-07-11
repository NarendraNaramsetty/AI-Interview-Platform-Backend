from django.urls import path
from .views import (
    StartInterviewView,
    ActiveInterviewView,
    PauseInterviewView,
    ResumeInterviewView,
    EndInterviewView,
    SaveAnswerView,
    NextQuestionView,
    NextQuestionAIView,
    PreviousQuestionView,
    SkipQuestionView,
    InterviewProgressView,
    InterviewHistoryView,
    InterviewDetailView,
    DuplicateInterviewView,
    TimelineEventsView
)

urlpatterns = [
    # Global interview configurations
    path('start', StartInterviewView.as_view(), name='interview_start'),
    path('current', ActiveInterviewView.as_view(), name='interview_current'),
    path('history', InterviewHistoryView.as_view(), name='interview_history'),
    
    # Specific session operations
    path('<int:id>', InterviewDetailView.as_view(), name='interview_detail'),
    path('<int:id>/pause', PauseInterviewView.as_view(), name='interview_pause'),
    path('<int:id>/resume', ResumeInterviewView.as_view(), name='interview_resume'),
    path('<int:id>/end', EndInterviewView.as_view(), name='interview_end'),
    path('<int:id>/answer', SaveAnswerView.as_view(), name='interview_answer'),
    
    # Flow navigation pointers
    path('<int:id>/next', NextQuestionView.as_view(), name='interview_next'),
    path('<int:id>/next-question', NextQuestionAIView.as_view(), name='interview_next_question'),
    path('<int:id>/previous', PreviousQuestionView.as_view(), name='interview_previous'),
    path('<int:id>/skip', SkipQuestionView.as_view(), name='interview_skip'),
    
    # Status metrics and replications
    path('<int:id>/progress', InterviewProgressView.as_view(), name='interview_progress'),
    path('<int:id>/duplicate', DuplicateInterviewView.as_view(), name='interview_duplicate'),
    path('<int:id>/timeline', TimelineEventsView.as_view(), name='interview_timeline'),
]
