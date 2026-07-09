from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import (
    QuestionCategoryViewSet,
    CompanyViewSet,
    JobRoleViewSet,
    TopicViewSet,
    InterviewQuestionViewSet,
    SearchQuestionsView,
    RandomQuestionsView,
    ImportQuestionsView,
    ExportQuestionsView,
    DuplicateQuestionView,
    QuestionAttachmentsView,
    QuestionAttachmentDeleteView,
    QuestionHistoryView
)

router = DefaultRouter(trailing_slash=False)
router.register('categories', QuestionCategoryViewSet, basename='category')
router.register('companies', CompanyViewSet, basename='company')
router.register('roles', JobRoleViewSet, basename='role')
router.register('topics', TopicViewSet, basename='topic')
router.register('', InterviewQuestionViewSet, basename='interview-question')

urlpatterns = [
    # Custom operations paths with optional trailing slashes
    re_path(r'^search/?$', SearchQuestionsView.as_view(), name='questions_search'),
    re_path(r'^random/?$', RandomQuestionsView.as_view(), name='questions_random'),
    re_path(r'^import/?$', ImportQuestionsView.as_view(), name='questions_import'),
    re_path(r'^export/?$', ExportQuestionsView.as_view(), name='questions_export'),
    re_path(r'^(?P<id>\d+)/duplicate/?$', DuplicateQuestionView.as_view(), name='question_duplicate'),
    re_path(r'^(?P<id>\d+)/attachments/?$', QuestionAttachmentsView.as_view(), name='question_attachments'),
    re_path(r'^attachments/(?P<id>\d+)/?$', QuestionAttachmentDeleteView.as_view(), name='question_attachment_delete'),
    re_path(r'^(?P<id>\d+)/history/?$', QuestionHistoryView.as_view(), name='question_history'),
    
    # Router views (categories, companies, roles, topics, questions base)
    path('', include(router.urls)),
]
