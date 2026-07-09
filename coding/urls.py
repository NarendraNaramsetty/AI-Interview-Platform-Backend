from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CodingCategoryListView,
    CodingProblemViewSet,
    RandomProblemView,
    StartCodingSessionView,
    SaveCodeDraftView,
    SubmitCodeView,
    SubmissionHistoryListView,
    SubmissionDetailView,
    CodingStatisticsView,
    LeaderboardView,
    FavoriteProblemsListView,
    FavoriteProblemDetailView
)

router = DefaultRouter(trailing_slash=False)
router.register('problems', CodingProblemViewSet, basename='coding-problem')

urlpatterns = [
    re_path(r'^categories/?$', CodingCategoryListView.as_view(), name='coding_categories'),
    re_path(r'^problems/random/?$', RandomProblemView.as_view(), name='coding_random_problem'),
    re_path(r'^start/?$', StartCodingSessionView.as_view(), name='coding_start'),
    re_path(r'^save/?$', SaveCodeDraftView.as_view(), name='coding_save'),
    re_path(r'^submit/?$', SubmitCodeView.as_view(), name='coding_submit'),
    re_path(r'^history/?$', SubmissionHistoryListView.as_view(), name='coding_history'),
    re_path(r'^submissions/(?P<id>\d+)/?$', SubmissionDetailView.as_view(), name='coding_submission_detail'),
    re_path(r'^statistics/?$', CodingStatisticsView.as_view(), name='coding_statistics'),
    re_path(r'^leaderboard/?$', LeaderboardView.as_view(), name='coding_leaderboard'),
    re_path(r'^favorites/?$', FavoriteProblemsListView.as_view(), name='coding_favorites_list'),
    re_path(r'^favorites/(?P<problem_id>\d+)/?$', FavoriteProblemDetailView.as_view(), name='coding_favorites_detail'),
    
    # ViewSet routes (problems list/detail)
    path('', include(router.urls)),
]
