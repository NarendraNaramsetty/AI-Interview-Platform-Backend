from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .services import DashboardService

class DashboardStatsView(APIView):
    """
    GET /api/dashboard/stats
    Aggregates profile, resume, interview, coding, and learning roadmap statistics.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Dashboard Statistics",
        responses={200: OpenApiResponse(description="Calculated widget statistics")}
    )
    def get(self, request):
        stats = DashboardService.get_candidate_statistics(request.user)
        return Response({
            "success": True,
            "message": "Dashboard statistics retrieved.",
            "data": stats
        }, status=status.HTTP_200_OK)


class DashboardActivityView(APIView):
    """
    GET /api/dashboard/activity
    Assembles chronological timelines logs across multiple platform features.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Dashboard Activity Feed",
        responses={200: OpenApiResponse(description="Timeline items logs")}
    )
    def get(self, request):
        activities = DashboardService.get_recent_activity(request.user)
        return Response({
            "success": True,
            "message": "Dashboard activity feed retrieved.",
            "data": activities
        }, status=status.HTTP_200_OK)
