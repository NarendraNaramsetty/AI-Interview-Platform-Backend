from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from resume.models import Resume
from .models import (
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    InterviewProgress,
    InterviewResult,
    InterviewTimeline
)
from .permissions import IsInterviewOwnerOrAdmin
from .services import InterviewService
from .filters import InterviewSessionFilter
from .serializers import (
    InterviewSessionSerializer,
    InterviewQuestionSerializer,
    InterviewAnswerSerializer,
    InterviewProgressSerializer,
    InterviewResultSerializer,
    InterviewTimelineSerializer,
    StartInterviewSerializer,
    SaveAnswerSerializer,
    InterviewDetailSerializer
)

class StartInterviewView(APIView):
    """
    POST /api/interviews/start
    Configures and launches a new interview mock session.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Start Interview Session",
        description="Creates a new mock session and auto-generates career-specific questions.",
        request=StartInterviewSerializer,
        responses={
            201: OpenApiResponse(description="Interview session created successfully."),
            400: OpenApiResponse(description="Validation error.")
        }
    )
    def post(self, request):
        serializer = StartInterviewSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        resume_id = serializer.validated_data.get('resume_id')
        resume = None
        if resume_id:
            from django.shortcuts import get_object_or_404
            resume = get_object_or_404(Resume, id=resume_id, user=request.user)

        try:
            session = InterviewService.start_interview(
                user=request.user,
                target_role=serializer.validated_data['target_role'],
                target_company=serializer.validated_data['target_company'],
                interview_type=serializer.validated_data['interview_type'],
                difficulty=serializer.validated_data['difficulty'],
                interview_mode=serializer.validated_data['interview_mode'],
                language=serializer.validated_data['language'],
                total_questions=serializer.validated_data['total_questions'],
                duration_minutes=serializer.validated_data['duration_minutes'],
                resume=resume,
                tech_stack=serializer.validated_data.get('tech_stack', []),
                adaptive_mode=serializer.validated_data.get('adaptive_mode', True)
            )
            return Response({
                "success": True,
                "message": "Interview Started Successfully",
                "data": {
                    "id": session.id,
                    "uuid": session.uuid,
                    "title": session.title
                }
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": {"detail": e.messages}
            }, status=status.HTTP_400_BAD_REQUEST)


class ActiveInterviewView(APIView):
    """
    GET /api/interviews/current
    Returns the user's active session.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Active Session",
        description="Retrieves the current 'In Progress' session for the authenticated user.",
        responses={
            200: InterviewSessionSerializer,
            404: OpenApiResponse(description="No active interview session found.")
        }
    )
    def get(self, request):
        session = InterviewSession.objects.filter(
            user=request.user, 
            status='In Progress'
        ).order_by('-created_at').first()
        
        if not session:
            return Response({
                "success": False,
                "message": "No active interview session found.",
                "errors": {"detail": ["You have no session currently In Progress."]}
            }, status=status.HTTP_404_NOT_FOUND)
            
        serializer = InterviewSessionSerializer(session)
        return Response({
            "success": True,
            "message": "Active session fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class PauseInterviewView(APIView):
    """
    POST /api/interviews/{id}/pause
    Suspends timer tracking on the target session.
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewOwnerOrAdmin]

    @extend_schema(
        summary="Pause Session",
        description="Changes session status to 'Paused' and updates timeline.",
        responses={200: OpenApiResponse(description="Session paused.")}
    )
    def post(self, request, id):
        session = get_object_or_404(InterviewSession, pk=id)
        self.check_object_permissions(request, session)
        
        try:
            InterviewService.pause_interview(session)
            return Response({
                "success": True,
                "message": "Interview paused successfully.",
                "data": {}
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": {"detail": e.messages}
            }, status=status.HTTP_400_BAD_REQUEST)


class ResumeInterviewView(APIView):
    """
    POST /api/interviews/{id}/resume
    Re-enables active timer runs on the target session.
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewOwnerOrAdmin]

    @extend_schema(
        summary="Resume Session",
        description="Restores session status to 'In Progress' and updates timeline.",
        responses={200: OpenApiResponse(description="Session resumed.")}
    )
    def post(self, request, id):
        session = get_object_or_404(InterviewSession, pk=id)
        self.check_object_permissions(request, session)
        
        try:
            InterviewService.resume_interview(session)
            return Response({
                "success": True,
                "message": "Interview resumed successfully.",
                "data": {}
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": {"detail": e.messages}
            }, status=status.HTTP_400_BAD_REQUEST)


class EndInterviewView(APIView):
    """
    POST /api/interviews/{id}/end
    Concludes the session, locking further answer updates and generating reports.
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewOwnerOrAdmin]

    @extend_schema(
        summary="End Session",
        description="Updates session status to 'Completed' and initializes report evaluations.",
        responses={200: InterviewResultSerializer}
    )
    def post(self, request, id):
        session = get_object_or_404(InterviewSession, pk=id)
        self.check_object_permissions(request, session)
        
        try:
            result = InterviewService.end_interview(session)
            return Response({
                "success": True,
                "message": "Interview Completed Successfully",
                "data": InterviewResultSerializer(result).data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": {"detail": e.messages}
            }, status=status.HTTP_400_BAD_REQUEST)


class SaveAnswerView(APIView):
    """
    POST /api/interviews/{id}/answer
    Saves an answer record, validating audio files if uploaded.
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewOwnerOrAdmin]

    @extend_schema(
        summary="Save Answer Response",
        description="Saves a question response transcript (with optional audio file) and updates stats.",
        request=SaveAnswerSerializer,
        responses={201: InterviewAnswerSerializer}
    )
    def post(self, request, id):
        session = get_object_or_404(InterviewSession, pk=id)
        self.check_object_permissions(request, session)
        
        serializer = SaveAnswerSerializer(
            data=request.data, 
            context={'session_id': session.id, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        question_id = serializer.validated_data['question_id']
        question = get_object_or_404(InterviewQuestion, id=question_id)
        
        answer_text = serializer.validated_data.get('answer_text', '')
        audio_file = serializer.validated_data.get('audio_file')
        duration = serializer.validated_data.get('answer_duration', 0)
        
        try:
            answer = InterviewService.save_answer(
                session=session,
                question=question,
                answer_text=answer_text,
                audio_file=audio_file,
                answer_duration=duration
            )
            return Response({
                "success": True,
                "message": "Answer Saved Successfully",
                "data": InterviewAnswerSerializer(answer).data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": {"detail": e.messages}
            }, status=status.HTTP_400_BAD_REQUEST)


class NextQuestionView(APIView):
    """
    POST /api/interviews/{id}/next
    Increments current session pointer and returns the next prompt.
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewOwnerOrAdmin]

    @extend_schema(
        summary="Next Question Pointer",
        description="Moves sequence index pointer to the next scheduled question.",
        responses={
            200: InterviewQuestionSerializer,
            400: OpenApiResponse(description="Already at the last question.")
        }
    )
    def post(self, request, id):
        session = get_object_or_404(InterviewSession, pk=id)
        self.check_object_permissions(request, session)
        
        if session.current_question_index >= session.total_questions - 1:
            return Response({
                "success": False,
                "message": "Already at the last question.",
                "errors": {"index": ["Cannot increment sequence further."]}
            }, status=status.HTTP_400_BAD_REQUEST)
            
        session.current_question_index += 1
        session.save(update_fields=['current_question_index'])
        
        curr_q = session.questions.filter(sequence_number=session.current_question_index + 1).first()
        if curr_q:
            session.progress.current_question = curr_q
            session.progress.save()
            
        return Response({
            "success": True,
            "message": "Moved to next question.",
            "data": InterviewQuestionSerializer(curr_q).data
        }, status=status.HTTP_200_OK)


class NextQuestionAIView(APIView):
    """
    POST /api/interviews/{id}/next-question
    Invokes adaptive AI prompt to evaluate last answer and yield the next question.
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewOwnerOrAdmin]

    def post(self, request, id):
        session = get_object_or_404(InterviewSession, pk=id)
        self.check_object_permissions(request, session)

        try:
            # Query adaptive AI question pipeline
            ai_data = InterviewService.get_next_question_ai(session)
            
            return Response({
                "success": True,
                "message": "AI Next Question generated successfully.",
                "data": ai_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"AI evaluation failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PreviousQuestionView(APIView):
    """
    POST /api/interviews/{id}/previous
    Decrements pointer to return the previous question.
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewOwnerOrAdmin]

    @extend_schema(
        summary="Previous Question Pointer",
        description="Moves index pointer back to the previous question.",
        responses={
            200: InterviewQuestionSerializer,
            400: OpenApiResponse(description="Already at the first question.")
        }
    )
    def post(self, request, id):
        session = get_object_or_404(InterviewSession, pk=id)
        self.check_object_permissions(request, session)
        
        if session.current_question_index <= 0:
            return Response({
                "success": False,
                "message": "Already at the first question.",
                "errors": {"index": ["Cannot decrement sequence further."]}
            }, status=status.HTTP_400_BAD_REQUEST)
            
        session.current_question_index -= 1
        session.save(update_fields=['current_question_index'])
        
        curr_q = session.questions.filter(sequence_number=session.current_question_index + 1).first()
        if curr_q:
            session.progress.current_question = curr_q
            session.progress.save()
            
        return Response({
            "success": True,
            "message": "Moved to previous question.",
            "data": InterviewQuestionSerializer(curr_q).data
        }, status=status.HTTP_200_OK)


class SkipQuestionView(APIView):
    """
    POST /api/interviews/{id}/skip
    Logs skips and increments the session pointer.
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewOwnerOrAdmin]

    @extend_schema(
        summary="Skip Question Pointer",
        description="Skips the current question, logs timeline events, and shifts pointer index forward.",
        responses={200: InterviewQuestionSerializer}
    )
    def post(self, request, id):
        session = get_object_or_404(InterviewSession, pk=id)
        self.check_object_permissions(request, session)
        
        curr_q = session.questions.filter(sequence_number=session.current_question_index + 1).first()
        if curr_q:
            InterviewService.log_event(session, 'Question Skipped', f"Skipped question seq #{curr_q.sequence_number}.")
            
        if session.current_question_index >= session.total_questions - 1:
            return Response({
                "success": False,
                "message": "Already at the last question. Cannot skip further.",
                "errors": {"index": ["Cannot skip last question element."]}
            }, status=status.HTTP_400_BAD_REQUEST)
            
        session.current_question_index += 1
        session.save(update_fields=['current_question_index'])
        
        next_q = session.questions.filter(sequence_number=session.current_question_index + 1).first()
        if next_q:
            session.progress.current_question = next_q
            session.progress.save()
            
        return Response({
            "success": True,
            "message": "Question skipped successfully.",
            "data": InterviewQuestionSerializer(next_q).data
        }, status=status.HTTP_200_OK)


class InterviewProgressView(APIView):
    """
    GET /api/interviews/{id}/progress
    Returns percent completion, remaining loops, and timers.
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewOwnerOrAdmin]

    @extend_schema(
        summary="Get Session Progress",
        description="Returns detailed counters and percentages completed.",
        responses={200: InterviewProgressSerializer}
    )
    def get(self, request, id):
        session = get_object_or_404(InterviewSession, pk=id)
        self.check_object_permissions(request, session)
        
        progress = session.progress
        serializer = InterviewProgressSerializer(progress)
        return Response({
            "success": True,
            "message": "Progress fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class InterviewHistoryView(generics.ListAPIView):
    """
    GET /api/interviews/history
    Lists completed and past sessions with filters.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InterviewSessionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = InterviewSessionFilter
    ordering_fields = ['created_at', 'target_role', 'target_company', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        if self.request.user.is_staff:
            return InterviewSession.objects.all().select_related('result')
        return InterviewSession.objects.filter(user=self.request.user).select_related('result')

    @extend_schema(
        summary="List Interview History",
        description="Lists metadata records of past scheduled or completed sessions.",
        parameters=[
            OpenApiParameter(name="role", description="Filter by target job role.", required=False, type=str),
            OpenApiParameter(name="company", description="Filter by company.", required=False, type=str),
            OpenApiParameter(name="status", description="Filter by status.", required=False, type=str)
        ]
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Interview history retrieved successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)


class InterviewDetailView(APIView):
    """
    GET /api/interviews/{id}
    DELETE /api/interviews/{id}
    Retrieves full details of a session (with questions/answers/timelines) or deletes it.
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewOwnerOrAdmin]

    def get_object(self, pk):
        queryset = InterviewSession.objects.select_related('result', 'resume').prefetch_related('questions', 'answers', 'timeline_events')
        session = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(self.request, session)
        return session

    @extend_schema(
        summary="Get Session Details",
        description="Returns config parameters, nested questions, submitted answers, and timeline histories.",
        responses={200: InterviewDetailSerializer}
    )
    def get(self, request, id):
        session = self.get_object(id)
        serializer = InterviewDetailSerializer(session)
        return Response({
            "success": True,
            "message": "Interview session details fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete Session (Soft Delete)",
        description="Flags session deleted_at, excluding it from normal lists.",
        responses={200: OpenApiResponse(description="Interview deleted successfully.")}
    )
    def delete(self, request, id):
        session = self.get_object(id)
        session.delete()
        return Response({
            "success": True,
            "message": "Interview Deleted Successfully",
            "data": {}
        }, status=status.HTTP_200_OK)


class DuplicateInterviewView(APIView):
    """
    POST /api/interviews/{id}/duplicate
    Launches replication copies based on historic sessions settings.
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewOwnerOrAdmin]

    @extend_schema(
        summary="Duplicate Configuration Settings",
        description="Creates a new scheduled session utilizing identical job role and total question details.",
        responses={201: InterviewSessionSerializer}
    )
    def post(self, request, id):
        session = get_object_or_404(InterviewSession, pk=id)
        self.check_object_permissions(request, session)
        
        duplicated = InterviewService.duplicate_session(session)
        serializer = InterviewSessionSerializer(duplicated)
        return Response({
            "success": True,
            "message": "Interview duplicated successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class TimelineEventsView(APIView):
    """
    GET /api/interviews/{id}/timeline
    Lists auditable event registers.
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewOwnerOrAdmin]

    @extend_schema(
        summary="Get Timeline Events",
        description="Returns chronological timeline logs of session activities.",
        responses={200: InterviewTimelineSerializer(many=True)}
    )
    def get(self, request, id):
        session = get_object_or_404(InterviewSession, pk=id)
        self.check_object_permissions(request, session)
        
        events = session.timeline_events.all().order_by('timestamp')
        serializer = InterviewTimelineSerializer(events, many=True)
        return Response({
            "success": True,
            "message": "Timeline events retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
