from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, filters
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import UserProfile, UserStatistics, UserAchievement, UserPreference, Achievement
# pyrefly: ignore [missing-import]
from .permissions import IsSelf
from .services import UserService
from .filters import UserProfileFilter
from .serializers import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    AvatarUploadSerializer,
    UserStatisticsSerializer,
    UserAchievementSerializer,
    UserPreferenceSerializer,
    SkillItemSerializer,
    PublicProfileSerializer
)

User = get_user_model()

class UserProfileView(APIView):
    """
    GET /api/users/profile
    PUT /api/users/profile
    Retrieves or updates the authenticated user's profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get User Profile",
        description="Retrieves the detailed career and educational profile of the authenticated user.",
        responses={200: UserProfileSerializer}
    )
    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response({
            "success": True,
            "message": "Profile fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update User Profile",
        description="Updates profile parameters such as headline, skills, education, and social links.",
        request=UserProfileUpdateSerializer,
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(description="Validation error.")
        }
    )
    def put(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_profile = serializer.save()
        
        # Recalculate completion percentage
        updated_profile.save()
        
        return Response({
            "success": True,
            "message": "Profile Updated Successfully",
            "data": UserProfileSerializer(updated_profile).data
        }, status=status.HTTP_200_OK)


class AvatarUploadView(APIView):
    """
    POST /api/users/avatar
    Uploads a new profile picture, deleting the old picture file.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Upload User Avatar",
        description="Accepts JPG, PNG, or WEBP images up to 5MB, deleting the old avatar file.",
        request=AvatarUploadSerializer,
        responses={
            200: OpenApiResponse(description="Avatar replaced successfully."),
            400: OpenApiResponse(description="Invalid file size or format.")
        }
    )
    def post(self, request):
        serializer = AvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        avatar_file = serializer.validated_data['avatar']
        user = UserService.replace_user_avatar(request.user, avatar_file)
        
        return Response({
            "success": True,
            "message": "Profile picture updated successfully.",
            "data": {
                "profile_picture": user.profile_picture.url if user.profile_picture else None
            }
        }, status=status.HTTP_200_OK)


class UserStatisticsView(APIView):
    """
    GET /api/users/statistics
    Retrieves platform usage and performance statistics for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get User Statistics",
        description="Returns mock-supported statistics such as completed interviews, scores, and streaks.",
        responses={200: UserStatisticsSerializer}
    )
    def get(self, request):
        stats, _ = UserStatistics.objects.get_or_create(user=request.user)
        serializer = UserStatisticsSerializer(stats)
        return Response({
            "success": True,
            "message": "Statistics fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class AchievementsView(APIView):
    """
    GET /api/users/achievements
    Retrieves all earned achievements for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Earned Achievements",
        description="Lists all badges and achievement milestones unlocked by the user.",
        responses={200: UserAchievementSerializer(many=True)}
    )
    def get(self, request):
        earned = UserAchievement.objects.filter(user=request.user).select_related('achievement')
        serializer = UserAchievementSerializer(earned, many=True)
        return Response({
            "success": True,
            "message": "Achievements fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class LeaderboardView(generics.ListAPIView):
    """
    GET /api/users/leaderboard
    Returns a list of top user profiles based on scores or streaks.
    Supports filtering and search params.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = UserProfileFilter
    
    # Expose custom ordering parameters mapping
    ordering_fields = [
        'user__statistics__average_score', 
        'user__statistics__coding_passed', 
        'user__statistics__total_interviews', 
        'user__statistics__current_streak'
    ]
    ordering = ['-user__statistics__average_score']

    def get_queryset(self):
        return UserProfile.objects.select_related('user', 'user__statistics').filter(user__is_active=True)

    @extend_schema(
        summary="Get Leaderboard",
        description="Returns user profiles sorted by scores or streaks. Supports ordering, searching, and filters.",
        parameters=[
            OpenApiParameter(name="ordering", description="Order by: -user__statistics__average_score, -user__statistics__current_streak etc.", required=False, type=str),
            OpenApiParameter(name="username", description="Search by name or email.", required=False, type=str),
            OpenApiParameter(name="skills", description="Search by comma-separated skills list.", required=False, type=str)
        ]
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Leaderboard fetched successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)


class SkillsView(APIView):
    """
    GET /api/users/skills
    POST /api/users/skills
    List or add elements to user's structured JSON skills array.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="List User Skills",
        description="Retrieves the structured JSON array of developer skills.",
        responses={200: SkillItemSerializer(many=True)}
    )
    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response({
            "success": True,
            "message": "Skills retrieved successfully.",
            "data": profile.skills or []
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Add User Skill",
        description="Appends a new structured skill to the profile's JSON tag list.",
        request=SkillItemSerializer,
        responses={201: SkillItemSerializer}
    )
    def post(self, request):
        serializer = SkillItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        skills = profile.skills or []
        
        # Calculate next id increment
        next_id = max([s.get('id', 0) for s in skills] or [0]) + 1
        new_skill = {
            "id": next_id,
            "name": serializer.validated_data['name']
        }
        
        skills.append(new_skill)
        profile.skills = skills
        profile.save()
        
        return Response({
            "success": True,
            "message": "Skill added successfully.",
            "data": new_skill
        }, status=status.HTTP_201_CREATED)


class SkillsDetailView(APIView):
    """
    PUT /api/users/skills/{id}
    DELETE /api/users/skills/{id}
    Modifies or removes a skill inside the JSON field array.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Update User Skill",
        description="Updates the name of a specific skill element matching the ID index.",
        request=SkillItemSerializer,
        responses={
            200: SkillItemSerializer,
            404: OpenApiResponse(description="Skill ID not found.")
        }
    )
    def put(self, request, id):
        serializer = SkillItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        profile = get_object_or_404(UserProfile, user=request.user)
        skills = profile.skills or []
        
        found = False
        target_skill = None
        for s in skills:
            if s.get('id') == int(id):
                s['name'] = serializer.validated_data['name']
                target_skill = s
                found = True
                break
                
        if not found:
            return Response({
                "success": False,
                "message": f"Skill with ID {id} was not found on this profile.",
                "errors": {"id": [f"Skill ID {id} does not exist."]}
            }, status=status.HTTP_404_NOT_FOUND)
            
        profile.skills = skills
        profile.save()
        
        return Response({
            "success": True,
            "message": "Skill updated successfully.",
            "data": target_skill
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete User Skill",
        description="Removes a specific skill element matching the ID index.",
        responses={
            200: OpenApiResponse(description="Skill removed successfully."),
            404: OpenApiResponse(description="Skill ID not found.")
        }
    )
    def delete(self, request, id):
        profile = get_object_or_404(UserProfile, user=request.user)
        skills = profile.skills or []
        
        initial_length = len(skills)
        skills = [s for s in skills if s.get('id') != int(id)]
        
        if len(skills) == initial_length:
            return Response({
                "success": False,
                "message": f"Skill with ID {id} was not found on this profile.",
                "errors": {"id": [f"Skill ID {id} does not exist."]}
            }, status=status.HTTP_404_NOT_FOUND)
            
        profile.skills = skills
        profile.save()
        
        return Response({
            "success": True,
            "message": "Skill deleted successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)


class UserPreferenceView(APIView):
    """
    GET /api/users/preferences
    PUT /api/users/preferences
    Retrieves or updates user interface preference configurations.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get User Preferences",
        description="Retrieves dark mode settings, notification choices, and preferred themes.",
        responses={200: UserPreferenceSerializer}
    )
    def get(self, request):
        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(pref)
        return Response({
            "success": True,
            "message": "Preferences fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update User Preferences",
        description="Updates parameters like theme, language, and notification toggles.",
        request=UserPreferenceSerializer,
        responses={200: UserPreferenceSerializer}
    )
    def put(self, request):
        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(pref, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_pref = serializer.save()
        return Response({
            "success": True,
            "message": "Preferences updated successfully.",
            "data": UserPreferenceSerializer(updated_pref).data
        }, status=status.HTTP_200_OK)


class DashboardSummaryView(APIView):
    """
    GET /api/users/dashboard-summary
    Returns user progress summaries, streak counters, success rates, and next recommendations.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Dashboard Summary",
        description="Aggregates progress counters, streak metrics, average scores, and recommendation text.",
        responses={200: OpenApiResponse(description="Summary calculations returned successfully.")}
    )
    def get(self, request):
        summary = UserService.get_dashboard_summary(request.user)
        return Response({
            "success": True,
            "message": "Dashboard summary calculated successfully.",
            "data": summary
        }, status=status.HTTP_200_OK)


class PublicProfileView(APIView):
    """
    GET /api/users/{username}
    Retrieves safe, public-facing user profile parameters. Anonymous read allowed.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Get Public Profile",
        description="Retrieves a developer profile by lookup email or UUID, hiding sensitive parameters.",
        responses={
            200: PublicProfileSerializer,
            404: OpenApiResponse(description="User profile not found.")
        }
    )
    def get(self, request, username):
        # Look up by email (username) or uuid
        user = User.objects.filter(email=username).first()
        if not user:
            try:
                user = User.objects.filter(uuid=username).first()
            except ValueError:
                user = None
                
        if not user or not user.is_active:
            return Response({
                "success": False,
                "message": "User profile not found.",
                "errors": {"username": ["Profile does not exist or is inactive."]}
            }, status=status.HTTP_404_NOT_FOUND)
            
        profile, _ = UserProfile.objects.get_or_create(user=user)
        serializer = PublicProfileSerializer(profile)
        
        return Response({
            "success": True,
            "message": "Public profile fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
