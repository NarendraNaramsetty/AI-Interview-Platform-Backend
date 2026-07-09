from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from django_filters.rest_framework import DjangoFilterBackend
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.contrib.auth import get_user_model
import random

from .models import (
    CodingCategory,
    CodingProblem,
    CodeSubmission,
    CodingScore,
    CodingHistory,
    FavoriteProblem
)
from .permissions import IsOwnerOrAdmin
from .filters import CodingProblemFilter, CodeSubmissionFilter
from .services import CodingChallengeService
from .serializers import (
    StartSessionRequestSerializer,
    SaveDraftRequestSerializer,
    SubmitCodeRequestSerializer,
    CodingCategorySerializer,
    CodingProblemSerializer,
    CodingProblemDetailSerializer,
    CodeSubmissionSerializer,
    FavoriteProblemSerializer
)
from .constants import STATUS_ACCEPTED
from .pagination import PrepAIPagination

User = get_user_model()

class CodingCategoryListView(generics.ListAPIView):
    """
    GET /api/coding/categories
    Lists all active categories.
    """
    queryset = CodingCategory.objects.filter(is_active=True).order_by('display_order')
    serializer_class = CodingCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Categories retrieved successfully.",
            "data": serializer.data
        })


class CodingProblemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/coding/problems
    GET /api/coding/problems/{id}
    Retrieves lists or detail fields of coding challenges.
    """
    queryset = CodingProblem.objects.filter(is_active=True).select_related('category', 'company').prefetch_related('test_cases')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = CodingProblemFilter
    ordering_fields = ['created_at', 'points', 'acceptance_rate']
    ordering = ['created_at']
    search_fields = ['title', 'description', 'problem_statement']
    pagination_class = PrepAIPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CodingProblemDetailSerializer
        return CodingProblemSerializer


class RandomProblemView(APIView):
    """
    GET /api/coding/problems/random
    Selects and returns one random matching coding challenge.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Random Coding Challenge Selection",
        description="Picks a single random active coding problem matching search difficulty or category bounds.",
        parameters=[
            OpenApiParameter(name="difficulty", description="Easy / Medium / Hard difficulty", required=False, type=str),
            OpenApiParameter(name="category", description="Category ID", required=False, type=int),
            OpenApiParameter(name="company", description="Company ID", required=False, type=int)
        ],
        responses={200: CodingProblemDetailSerializer}
    )
    def get(self, request):
        difficulty = request.query_params.get('difficulty')
        category_id = request.query_params.get('category')
        company_id = request.query_params.get('company')

        queryset = CodingProblem.objects.filter(is_active=True)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        problem_ids = list(queryset.values_list('id', flat=True))
        if not problem_ids:
            return Response({
                "success": False,
                "message": "No matching coding problems found.",
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)

        random_id = random.choice(problem_ids)
        problem = CodingProblem.objects.get(pk=random_id)
        serializer = CodingProblemDetailSerializer(problem)
        return Response({
            "success": True,
            "message": "Random problem selected successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class StartCodingSessionView(APIView):
    """
    POST /api/coding/start
    Start session attempt. Logs audit timeline values.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Start Code Session Attempt",
        request=StartSessionRequestSerializer,
        responses={201: CodeSubmissionSerializer}
    )
    def post(self, request):
        serializer = StartSessionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        problem_id = serializer.validated_data['problem_id']

        try:
            draft = CodingChallengeService.start_coding_session(problem_id, request.user)
            response_serializer = CodeSubmissionSerializer(draft)
            return Response({
                "success": True,
                "message": "Coding session started successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_201_CREATED)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class SaveCodeDraftView(APIView):
    """
    POST /api/coding/save
    Auto-saves code draft files to submission status 'Pending'.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Auto-Save Code Draft",
        request=SaveDraftRequestSerializer,
        responses={200: CodeSubmissionSerializer}
    )
    def post(self, request):
        serializer = SaveDraftRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        problem_id = serializer.validated_data['problem_id']
        language = serializer.validated_data['programming_language']
        code = serializer.validated_data['source_code']

        try:
            draft = CodingChallengeService.save_code_draft(problem_id, language, code, request.user)
            response_serializer = CodeSubmissionSerializer(draft)
            return Response({
                "success": True,
                "message": "Code draft autosaved successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_200_OK)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class SubmitCodeView(APIView):
    """
    POST /api/coding/submit
    Final submit source code. Evaluates mock score parameters.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Submit Code Solution",
        request=SubmitCodeRequestSerializer,
        responses={201: CodeSubmissionSerializer}
    )
    def post(self, request):
        serializer = SubmitCodeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        problem_id = serializer.validated_data['problem_id']
        language = serializer.validated_data['programming_language']
        code = serializer.validated_data['source_code']

        try:
            submission = CodingChallengeService.submit_code(problem_id, language, code, request.user)
            response_serializer = CodeSubmissionSerializer(submission)
            return Response({
                "success": True,
                "message": "Code submitted successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_201_CREATED)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class SubmissionHistoryListView(generics.ListAPIView):
    """
    GET /api/coding/history
    List previous submissions for the current candidate. Admins see all.
    Supports filtering by language, status, dates, search, and pagination.
    """
    serializer_class = CodeSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = CodeSubmissionFilter
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    search_fields = ['problem__title', 'source_code']
    pagination_class = PrepAIPagination

    def get_queryset(self):
        user = self.request.user
        queryset = CodeSubmission.objects.select_related('problem', 'user', 'score_record').prefetch_related('history_logs')
        if user.is_staff:
            return queryset
        return queryset.filter(user=user)


class SubmissionDetailView(generics.RetrieveAPIView):
    """
    GET /api/coding/submissions/{id}
    Retrieves full metrics scorecard details for a specific submission.
    """
    queryset = CodeSubmission.objects.select_related('problem', 'user', 'score_record').prefetch_related('history_logs')
    serializer_class = CodeSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    lookup_field = 'id'


class CodingStatisticsView(APIView):
    """
    GET /api/coding/statistics
    Retrieves streaks data, difficulty breakdown, solved counts.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Coding Stats Dashboard",
        responses={200: OpenApiResponse(description="Calculated stats dictionary")}
    )
    def get(self, request):
        stats = CodingChallengeService.get_coding_statistics(request.user)
        return Response({
            "success": True,
            "message": "Coding statistics retrieved successfully.",
            "data": stats
        }, status=status.HTTP_200_OK)


class LeaderboardView(APIView):
    """
    GET /api/coding/leaderboard
    Overall, weekly, and monthly ranking scoreboards based on total points.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Leaderboard Rankings",
        parameters=[
            OpenApiParameter(name="period", description="overall, weekly, or monthly", required=False, type=str, default='overall')
        ]
    )
    def get(self, request):
        period = request.query_params.get('period', 'overall')
        queryset = User.objects.all()
        now = timezone.now()

        # Build date limits logic
        if period == 'weekly':
            date_limit = now - timezone.timedelta(days=7)
            queryset = queryset.filter(
                coding_submissions__created_at__gte=date_limit,
                coding_submissions__status=STATUS_ACCEPTED
            )
        elif period == 'monthly':
            date_limit = now - timezone.timedelta(days=30)
            queryset = queryset.filter(
                coding_submissions__created_at__gte=date_limit,
                coding_submissions__status=STATUS_ACCEPTED
            )
        else:
            queryset = queryset.filter(
                coding_submissions__status=STATUS_ACCEPTED
            )

        # Annotate points
        queryset = queryset.annotate(
            total_points=Sum('coding_submissions__score_record__ranking_points')
        ).filter(total_points__gt=0).order_by('-total_points')

        # Limit to top 50
        data = []
        rank = 1
        for u in queryset[:50]:
            data.append({
                "rank": rank,
                "user_id": u.id,
                "name": f"{u.first_name} {u.last_name}".strip() or u.email,
                "points": u.total_points
            })
            rank += 1

        return Response({
            "success": True,
            "message": f"Leaderboard for {period} fetched successfully.",
            "data": data
        }, status=status.HTTP_200_OK)


class FavoriteProblemsListView(generics.ListAPIView):
    """
    GET /api/coding/favorites
    Lists favorited coding problems for the candidate.
    """
    serializer_class = FavoriteProblemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return FavoriteProblem.objects.filter(user=self.request.user).select_related('problem').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Favorite problems retrieved successfully.",
            "data": serializer.data
        })


class FavoriteProblemDetailView(APIView):
    """
    POST /api/coding/favorites/{problem_id}
    DELETE /api/coding/favorites/{problem_id}
    Bookmarks/favorites coding challenges.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Add/Remove Favorite Bookmark",
        responses={
            201: OpenApiResponse(description="Problem bookmarked successfully."),
            200: OpenApiResponse(description="Problem removed from favorites.")
        }
    )
    def post(self, request, problem_id):
        problem = get_object_or_404(CodingProblem, pk=problem_id)
        fav, created = FavoriteProblem.objects.get_or_create(
            user=request.user,
            problem=problem
        )
        if not created:
            return Response({
                "success": True,
                "message": "Problem is already in favorites.",
                "data": FavoriteProblemSerializer(fav).data
            }, status=status.HTTP_200_OK)

        return Response({
            "success": True,
            "message": "Problem added to favorites successfully.",
            "data": FavoriteProblemSerializer(fav).data
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, problem_id):
        problem = get_object_or_404(CodingProblem, pk=problem_id)
        fav = FavoriteProblem.objects.filter(user=request.user, problem=problem).first()
        if not fav:
            return Response({
                "success": False,
                "message": "Problem is not in favorites.",
                "data": {}
            }, status=status.HTTP_400_BAD_REQUEST)

        fav.delete()
        return Response({
            "success": True,
            "message": "Problem removed from favorites successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)
