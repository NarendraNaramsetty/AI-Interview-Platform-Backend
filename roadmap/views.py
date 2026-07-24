from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from django_filters.rest_framework import DjangoFilterBackend
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from .models import (
    CareerPath,
    Roadmap,
    RoadmapModule,
    LearningResource,
    UserRoadmap,
    ModuleProgress,
    LearningReminder,
    RoadmapPathway,
    RoadmapMilestone
)
from .permissions import IsOwnerOrAdmin
from .filters import RoadmapFilter, LearningResourceFilter
from .services import RoadmapService, RoadmapAnalyticsService
from .pagination import PrepAIPagination
from .serializers import (
    StartRoadmapRequestSerializer,
    UpdateProgressRequestSerializer,
    RoadmapActionRequestSerializer,
    CareerPathSerializer,
    LearningResourceSerializer,
    RoadmapSerializer,
    RoadmapDetailSerializer,
    UserRoadmapSerializer,
    LearningReminderSerializer,
    RoadmapPathwaySerializer,
    RoadmapPathwayListSerializer,
    RoadmapGenerateRequestSerializer,
    MilestoneProgressUpdateSerializer
)
from .constants import STATUS_IN_PROGRESS, STATUS_COMPLETED



class RoadmapGenerateView(APIView):
    """
    Generate a personalized learning roadmap based on user interest.
    Takes minimal input (just interest text) and uses LLM to infer level and milestones.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = RoadmapGenerateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interest_text = serializer.validated_data.get('interest')
        self_described_exp = serializer.validated_data.get('self_described_experience', '')
        resume_context = serializer.validated_data.get('resume_context', '')
        
        try:
            pathway = RoadmapService.create_pathway_from_interest(
                user=request.user,
                interest_text=interest_text,
                self_described_experience=self_described_exp or None,
                resume_context_summary=resume_context or None
            )
            
            pathway_serializer = RoadmapPathwaySerializer(pathway)
            return Response(
                {
                    'status': 'success',
                    'message': 'Roadmap generated successfully',
                    'data': pathway_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
            
        except ValueError as e:
            return Response(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': f'Error generating roadmap: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RoadmapPathwayListView(APIView):
    """List all roadmap pathways for the authenticated user."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        pathways = RoadmapService.get_user_pathways(request.user)
        serializer = RoadmapPathwayListSerializer(pathways, many=True)
        
        return Response(
            {
                'status': 'success',
                'count': len(pathways),
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )


class RoadmapPathwayDetailView(APIView):
    """Get details of a specific roadmap pathway."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pathway_id):
        pathway = RoadmapService.get_pathway_with_milestones(pathway_id, request.user)
        
        if not pathway:
            return Response(
                {
                    'status': 'error',
                    'message': 'Pathway not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = RoadmapPathwaySerializer(pathway)
        return Response(
            {
                'status': 'success',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )


class MilestoneCompleteView(APIView):
    """Update milestone progress (mark complete or update progress %)."""
    
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, pathway_id, milestone_id):
        pathway = RoadmapService.get_pathway_with_milestones(pathway_id, request.user)
        
        if not pathway:
            return Response(
                {
                    'status': 'error',
                    'message': 'Pathway not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        milestone = get_object_or_404(
            RoadmapMilestone,
            id=milestone_id,
            pathway=pathway
        )
        
        serializer = MilestoneProgressUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            progress_percent = serializer.validated_data.get('progress_percent')
            is_completed = serializer.validated_data.get('is_completed')
            
            milestone = RoadmapService.update_milestone_progress(
                milestone,
                progress_percent=progress_percent,
                is_completed=is_completed
            )
            
            from .serializers import RoadmapMilestoneSerializer
            milestone_serializer = RoadmapMilestoneSerializer(milestone)
            
            return Response(
                {
                    'status': 'success',
                    'message': 'Milestone updated',
                    'data': milestone_serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class RoadmapDeleteView(APIView):
    """Delete a roadmap pathway."""
    
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pathway_id):
        pathway = RoadmapService.get_pathway_with_milestones(pathway_id, request.user)
        
        if not pathway:
            return Response(
                {
                    'status': 'error',
                    'message': 'Pathway not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        pathway_title = pathway.pathway_title
        
        try:
            RoadmapService.delete_pathway(pathway)
            return Response(
                {
                    'status': 'success',
                    'message': f'Pathway "{pathway_title}" deleted'
                },
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RoadmapStatisticsView(APIView):
    """Get roadmap statistics for the user."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        stats = RoadmapAnalyticsService.get_user_roadmap_summary(request.user)
        difficulty_breakdown = RoadmapAnalyticsService.get_learning_difficulty_breakdown(request.user)
        avg_readiness = RoadmapAnalyticsService.get_average_readiness_progress(request.user)
        recent = RoadmapAnalyticsService.get_most_recent_pathways(request.user, limit=5)
        
        return Response(
            {
                'status': 'success',
                'data': {
                    'summary': stats,
                    'difficulty_breakdown': difficulty_breakdown,
                    'average_readiness': avg_readiness,
                    'recent_pathways': recent,
                }
            },
            status=status.HTTP_200_OK
        )



class GeneratePersonalizedRoadmapView(APIView):
    """
    POST /api/roadmap/generate-ai
    Generates a personalized learning roadmap using AI and returns the UserRoadmap.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        interest = request.data.get('interest') or request.data.get('career_track') or ''
        experience_level = request.data.get('experience_level', 'Beginner')
        target_company = request.data.get('target_company', '')
        weekly_hours = request.data.get('weekly_hours', '')
        preferred_learning_style = request.data.get('preferred_learning_style', [])

        if not interest:
            return Response(
                {"success": False, "message": "Interest is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        experience_info = f"Experience: {experience_level}. Target: {target_company}. Weekly hours: {weekly_hours}. Styles: {', '.join(preferred_learning_style)}."

        try:
            from django.db import transaction
            from .models import CareerPath, Roadmap, RoadmapModule, UserRoadmap, ModuleProgress
            from .constants import STATUS_IN_PROGRESS

            # First: Search pre-seeded database bank for matching CareerPath / Roadmap
            interest_clean = interest.strip()
            
            # Split multi-role inputs if any (e.g., "Full Stack Developer & Frontend Developer")
            primary_role = interest_clean.split('&')[0].strip() if '&' in interest_clean else interest_clean
            
            seeded_roadmap = (
                Roadmap.objects.filter(career_path__name__iexact=primary_role, total_modules__gt=0).first() or
                Roadmap.objects.filter(title__iexact=f"{primary_role} Roadmap", total_modules__gt=0).first() or
                Roadmap.objects.filter(career_path__name__icontains=primary_role, total_modules__gt=0).order_by('-total_modules').first() or
                Roadmap.objects.filter(title__icontains=primary_role, total_modules__gt=0).order_by('-total_modules').first()
            )

            if seeded_roadmap and seeded_roadmap.modules.exists():
                with transaction.atomic():
                    # Deactivate any previous active UserRoadmap for this user
                    UserRoadmap.objects.filter(
                        user=request.user, 
                        status=STATUS_IN_PROGRESS
                    ).update(status='Paused')

                    first_module = seeded_roadmap.modules.order_by('module_order', 'id').first()

                    user_roadmap = UserRoadmap.objects.create(
                        user=request.user,
                        roadmap=seeded_roadmap,
                        status=STATUS_IN_PROGRESS,
                        current_module=first_module,
                        progress_percentage=0.0,
                        completed_modules=0
                    )

                    # Create ModuleProgress for each module
                    progresses = [
                        ModuleProgress(
                            user_roadmap=user_roadmap,
                            roadmap_module=module,
                            is_completed=False
                        )
                        for module in seeded_roadmap.modules.all()
                    ]
                    ModuleProgress.objects.bulk_create(progresses, ignore_conflicts=True)

                from .serializers import UserRoadmapSerializer
                response_serializer = UserRoadmapSerializer(user_roadmap, context={'request': request})
                return Response({
                    "success": True,
                    "message": f"Pre-seeded curriculum loaded for '{seeded_roadmap.career_path.name}'.",
                    "data": response_serializer.data
                }, status=status.HTTP_200_OK)

            # Second: Fallback to LLM dynamic generation if no pre-seeded roadmap matched
            from nlp.utils.roadmap_generator import generate_roadmap

            roadmap_data = generate_roadmap(
                user_interest_text=interest,
                self_described_experience=experience_info
            )

            with transaction.atomic():
                # Deactivate any previous active UserRoadmap
                UserRoadmap.objects.filter(
                    user=request.user, 
                    status=STATUS_IN_PROGRESS
                ).update(status='Paused')

                # Find or create a CareerPath
                career_path_name = f"{roadmap_data.get('pathway_title', interest)[:140]}"
                career_path, _ = CareerPath.objects.get_or_create(
                    name=career_path_name,
                    defaults={
                        "description": f"Custom learning path for {interest}",
                        "difficulty": roadmap_data.get('inferred_starting_level', 'Medium'),
                        "estimated_duration": "Variable"
                    }
                )

                # Create the Roadmap template
                import json
                description_payload = {
                    "inferred_level_reason": roadmap_data.get("inferred_level_reason", ""),
                    "prerequisites": roadmap_data.get("prerequisites", []),
                    "preparation_guide": roadmap_data.get("preparation_guide", {})
                }
                
                duration_hours = sum(m.get('estimated_hours', 10) for m in roadmap_data.get('milestones', []))
                roadmap = Roadmap.objects.create(
                    title=roadmap_data.get('pathway_title', f"Roadmap - {interest}"),
                    description=json.dumps(description_payload),
                    career_path=career_path,
                    estimated_duration=f"{duration_hours} hours",
                    total_modules=len(roadmap_data.get('milestones', [])),
                    difficulty=roadmap_data.get('inferred_starting_level', 'Medium')
                )

                # Create RoadmapModules & ModuleProgresses
                first_module = None
                modules = []
                for milestone in roadmap_data.get('milestones', []):
                    module = RoadmapModule.objects.create(
                        roadmap=roadmap,
                        title=milestone.get('title', 'Module'),
                        description=f"{milestone.get('description', '')}\n\nWhy it matters: {milestone.get('why_it_matters', '')}\n\nKey topics: {', '.join(milestone.get('key_topics', []))}",
                        module_order=milestone.get('milestone_number', 1),
                        estimated_hours=milestone.get('estimated_hours', 10),
                        difficulty=milestone.get('difficulty_tag', 'Medium')
                    )
                    modules.append(module)
                    if not first_module:
                        first_module = module

                # Create UserRoadmap
                user_roadmap = UserRoadmap.objects.create(
                    user=request.user,
                    roadmap=roadmap,
                    status=STATUS_IN_PROGRESS,
                    current_module=first_module,
                    progress_percentage=0.0,
                    completed_modules=0
                )

                # Create initial progress tracker for each module
                for module in modules:
                    ModuleProgress.objects.create(
                        user_roadmap=user_roadmap,
                        roadmap_module=module,
                        is_completed=False
                    )

            from .serializers import UserRoadmapSerializer
            response_serializer = UserRoadmapSerializer(user_roadmap, context={'request': request})
            return Response({
                "success": True,
                "message": "Curriculum Generated successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": f"Roadmap Generation Error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RoadmapMentorView(APIView):
    """
    POST /api/roadmap/mentor
    AI mentoring and career advice for a specific module.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        module_id = request.data.get('module_id')
        message = request.data.get('message', '')

        if not module_id or not message:
            return Response(
                {"success": False, "message": "module_id and message are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .models import RoadmapModule
        module = get_object_or_404(RoadmapModule, id=module_id)

        mentor_prompt = f"""You are an expert AI Career Coach.
The user is learning the module \"{module.title}\" (Difficulty: {module.difficulty}) inside their roadmap \"{module.roadmap.title}\".
User Question: \"{message}\"

Please provide a helpful, clean explanation or solution outline. Use markdown formatting. Keep the output under 15 lines."""

        try:
            from ai_core.services import AIService
            res = AIService.route_request("Chat", mentor_prompt, request.user)
            reply = res.get("response", "AI Mentor response compiled.")
            
            # Log the request
            try:
                AIService.log_request(
                    user=request.user,
                    module_name="roadmap",
                    request_type="Chat",
                    provider=res.get("provider", "Gemini"),
                    model=res.get("model", "default"),
                    prompt_length=len(mentor_prompt),
                    response_length=len(reply),
                    execution_time=1.0,
                    token_usage=res.get("token_usage", 0),
                    request_status="Success"
                )
            except Exception:
                pass

            return Response({
                "reply": reply
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "reply": f"Sorry, AI Mentor connection error: {str(e)}"
            }, status=status.HTTP_200_OK)


class CareerPathListView(generics.ListAPIView):
    """
    GET /api/roadmap/careers
    Lists all active career paths.
    """
    queryset = CareerPath.objects.filter(is_active=True)
    serializer_class = CareerPathSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Careers retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class RoadmapViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/roadmap
    GET /api/roadmap/{id}
    Lists or details roadmaps templates.
    """
    queryset = Roadmap.objects.filter(is_active=True).select_related('career_path')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = RoadmapFilter
    ordering_fields = ['created_at', 'title']
    ordering = ['title']
    search_fields = ['title', 'description']
    pagination_class = PrepAIPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RoadmapDetailSerializer
        return RoadmapSerializer


class StartRoadmapView(APIView):
    """
    POST /api/roadmap/start
    Enrolls a candidate user into a roadmap program.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Start Roadmap Enrolment",
        request=StartRoadmapRequestSerializer,
        responses={201: UserRoadmapSerializer}
    )
    def post(self, request):
        serializer = StartRoadmapRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        roadmap_id = serializer.validated_data['roadmap_id']

        try:
            user_roadmap = RoadmapService.start_roadmap(roadmap_id, request.user)
            response_serializer = UserRoadmapSerializer(user_roadmap)
            return Response({
                "success": True,
                "message": "Roadmap started successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_201_CREATED)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class UpdateProgressView(APIView):
    """
    PUT /api/roadmap/progress
    Updates module progress completions states.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Update Module Learning Progress",
        request=UpdateProgressRequestSerializer,
        responses={200: UserRoadmapSerializer}
    )
    def put(self, request):
        serializer = UpdateProgressRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_roadmap_id = serializer.validated_data['user_roadmap_id']
        module_id = serializer.validated_data['module_id']
        is_completed = serializer.validated_data.get('is_completed')
        is_bookmarked = serializer.validated_data.get('is_bookmarked')
        notes = serializer.validated_data.get('notes')

        try:
            user_roadmap = RoadmapService.update_module_progress(
                user_roadmap_id=user_roadmap_id,
                module_id=module_id,
                is_completed=is_completed,
                is_bookmarked=is_bookmarked,
                notes=notes,
                user=request.user
            )
            response_serializer = UserRoadmapSerializer(user_roadmap)
            return Response({
                "success": True,
                "message": "Module progress updated successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_200_OK)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class PauseRoadmapView(APIView):
    """
    POST /api/roadmap/pause
    Pauses active roadmap learning routines.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Pause Active Roadmap",
        request=RoadmapActionRequestSerializer,
        responses={200: UserRoadmapSerializer}
    )
    def post(self, request):
        serializer = RoadmapActionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        roadmap_id = serializer.validated_data['roadmap_id']

        try:
            user_roadmap = RoadmapService.pause_roadmap(roadmap_id, request.user)
            response_serializer = UserRoadmapSerializer(user_roadmap)
            return Response({
                "success": True,
                "message": "Roadmap paused successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_200_OK)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class ResumeRoadmapView(APIView):
    """
    POST /api/roadmap/resume
    Resumes paused roadmap progress.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Resume Paused Roadmap",
        request=RoadmapActionRequestSerializer,
        responses={200: UserRoadmapSerializer}
    )
    def post(self, request):
        serializer = RoadmapActionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        roadmap_id = serializer.validated_data['roadmap_id']

        try:
            user_roadmap = RoadmapService.resume_roadmap(roadmap_id, request.user)
            response_serializer = UserRoadmapSerializer(user_roadmap)
            return Response({
                "success": True,
                "message": "Roadmap resumed successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_200_OK)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class CurrentRoadmapView(APIView):
    """
    GET /api/roadmap/current
    Returns currently active UserRoadmap (status: 'In Progress').
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Current Active Roadmap Progress",
        responses={200: UserRoadmapSerializer}
    )
    def get(self, request):
        current_roadmap = UserRoadmap.objects.filter(
            user=request.user, 
            status=STATUS_IN_PROGRESS
        ).select_related('roadmap').first()
        
        if not current_roadmap:
            return Response({
                "success": True,
                "message": "No active roadmap found.",
                "data": None
            }, status=status.HTTP_200_OK)

        serializer = UserRoadmapSerializer(current_roadmap)
        return Response({
            "success": True,
            "message": "Current roadmap retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class CompletedRoadmapsListView(generics.ListAPIView):
    """
    GET /api/roadmap/completed
    Lists completed roadmaps templates for the candidate.
    """
    serializer_class = UserRoadmapSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return UserRoadmap.objects.filter(
            user=self.request.user, 
            status=STATUS_COMPLETED
        ).select_related('roadmap')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Completed roadmaps retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class LearningResourceListView(generics.ListAPIView):
    """
    GET /api/roadmap/resources
    Returns learning study resources filtered by type, provider, or free/paid.
    """
    queryset = LearningResource.objects.all()
    serializer_class = LearningResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = LearningResourceFilter
    search_fields = ['title', 'provider']
    pagination_class = PrepAIPagination

    # Wrap the paginated response in standard success envelope
    # Note: DRF's list triggers paginate_queryset which hooks into PrepAIPagination.


class LearningStatisticsView(APIView):
    """
    GET /api/roadmap/statistics
    Returns user learning metrics stats.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get learning progress statistics",
        responses={200: OpenApiResponse(description="Calculated statistics values")}
    )
    def get(self, request):
        stats = RoadmapService.get_roadmap_statistics(request.user)
        return Response({
            "success": True,
            "message": "Learning statistics retrieved successfully.",
            "data": stats
        }, status=status.HTTP_200_OK)


class LearningReminderViewSet(viewsets.ModelViewSet):
    """
    GET /api/roadmap/reminders
    POST /api/roadmap/reminders
    PUT /api/roadmap/reminders/{id}
    DELETE /api/roadmap/reminders/{id}
    """
    serializer_class = LearningReminderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    lookup_field = 'id'

    def get_queryset(self):
        return LearningReminder.objects.filter(user=self.request.user).select_related('roadmap')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Reminders retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "success": True,
            "message": "Learning reminder created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "success": True,
            "message": "Learning reminder updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "success": True,
            "message": "Learning reminder deleted successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)
