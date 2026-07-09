from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from django_filters.rest_framework import DjangoFilterBackend
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from .models import (
    InterviewEvaluation,
    TechnicalEvaluation,
    CommunicationEvaluation,
    HRBehaviorEvaluation,
    OverallEvaluation,
    ImprovementSuggestion,
    RecommendedResource,
    EvaluationHistory
)
from .permissions import IsOwnerOrAdmin
from .filters import InterviewEvaluationFilter
from .services import QuestionEvaluationService
from .serializers import (
    GenerateEvaluationRequestSerializer,
    InterviewEvaluationSerializer,
    TechnicalEvaluationSerializer,
    CommunicationEvaluationSerializer,
    HRBehaviorEvaluationSerializer,
    OverallEvaluationSerializer,
    ImprovementSuggestionSerializer,
    RecommendedResourceSerializer,
    EvaluationHistorySerializer
)

class InterviewEvaluationListView(generics.ListAPIView):
    """
    GET /api/feedback
    Lists evaluations. Users see only their own evaluations. Admins see all.
    Supports filtering by status, overall rating, score range, date range, ordering, search, and pagination.
    """
    serializer_class = InterviewEvaluationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = InterviewEvaluationFilter
    ordering_fields = ['created_at', 'evaluated_at', 'overall_evaluation__overall_score']
    ordering = ['-evaluated_at']
    search_fields = ['interview__title', 'interview__target_role', 'interview__target_company']

    def get_queryset(self):
        user = self.request.user
        queryset = InterviewEvaluation.objects.select_related(
            'interview', 'user', 'technical_evaluation', 
            'communication_evaluation', 'hr_evaluation', 'overall_evaluation'
        ).prefetch_related('suggestions', 'resources', 'history_logs')
        
        if user.is_staff:
            return queryset
        return queryset.filter(user=user)


class GenerateEvaluationView(APIView):
    """
    POST /api/feedback/generate
    Trigger evaluation generation for a completed interview session.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Generate AI Evaluation Card",
        description="Creates placeholder evaluation parameters for a completed candidate session.",
        request=GenerateEvaluationRequestSerializer,
        responses={
            201: OpenApiResponse(description="Evaluation Generated Successfully", response=InterviewEvaluationSerializer),
            400: OpenApiResponse(description="Validation Error")
        }
    )
    def post(self, request):
        serializer = GenerateEvaluationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interview_id = serializer.validated_data['interview_id']

        try:
            evaluation = QuestionEvaluationService.generate_evaluation_for_interview(
                interview_id=interview_id,
                user=request.user
            )
            response_serializer = InterviewEvaluationSerializer(evaluation)
            return Response({
                "success": True,
                "message": "Evaluation Generated Successfully",
                "data": response_serializer.data
            }, status=status.HTTP_201_CREATED)
        except (DjangoValidationError, DRFValidationError) as e:
            if isinstance(e, DjangoValidationError):
                err_detail = e.message_dict if hasattr(e, 'message_dict') else {"detail": e.messages}
            else:
                err_detail = e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class EvaluationBaseView(APIView):
    """
    Helper base class retrieving the main evaluation record linked to an interview_id
    and checking proper ownership access controls.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_evaluation(self, interview_id):
        evaluation = get_object_or_404(
            InterviewEvaluation.objects.select_related(
                'interview', 'user', 'technical_evaluation', 
                'communication_evaluation', 'hr_evaluation', 'overall_evaluation'
            ).prefetch_related('suggestions', 'resources', 'history_logs'),
            interview_id=interview_id
        )
        # Perform ownership checks
        self.check_object_permissions(self.request, evaluation)
        return evaluation


class InterviewEvaluationDetailView(EvaluationBaseView):
    """
    GET /api/feedback/{interview_id}
    Retrieves the complete report card including nested scores, suggestions, courses, and logs.
    """
    @extend_schema(
        summary="Get Complete Evaluation Report Card",
        description="Retrieves candidate report card mapped by domains, resource tips, and history logs.",
        responses={200: InterviewEvaluationSerializer}
    )
    def get(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        serializer = InterviewEvaluationSerializer(evaluation)
        return Response({
            "success": True,
            "message": "Evaluation fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class TechnicalEvaluationDetailView(EvaluationBaseView):
    """
    GET /api/feedback/{interview_id}/technical
    PUT /api/feedback/{interview_id}/technical
    """
    @extend_schema(
        summary="Get Technical Scores",
        responses={200: TechnicalEvaluationSerializer}
    )
    def get(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        serializer = TechnicalEvaluationSerializer(evaluation.technical_evaluation)
        return Response({
            "success": True,
            "message": "Technical evaluation retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update Technical Scores",
        request=TechnicalEvaluationSerializer,
        responses={200: TechnicalEvaluationSerializer}
    )
    def put(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        technical_eval = evaluation.technical_evaluation
        serializer = TechnicalEvaluationSerializer(technical_eval, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Technical evaluation updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class CommunicationEvaluationDetailView(EvaluationBaseView):
    """
    GET /api/feedback/{interview_id}/communication
    PUT /api/feedback/{interview_id}/communication
    """
    @extend_schema(
        summary="Get Communication Scores",
        responses={200: CommunicationEvaluationSerializer}
    )
    def get(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        serializer = CommunicationEvaluationSerializer(evaluation.communication_evaluation)
        return Response({
            "success": True,
            "message": "Communication evaluation retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update Communication Scores",
        request=CommunicationEvaluationSerializer,
        responses={200: CommunicationEvaluationSerializer}
    )
    def put(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        communication_eval = evaluation.communication_evaluation
        serializer = CommunicationEvaluationSerializer(communication_eval, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Communication evaluation updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class HRBehaviorEvaluationDetailView(EvaluationBaseView):
    """
    GET /api/feedback/{interview_id}/hr
    PUT /api/feedback/{interview_id}/hr
    """
    @extend_schema(
        summary="Get HR/Behavioral Assessment",
        responses={200: HRBehaviorEvaluationSerializer}
    )
    def get(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        serializer = HRBehaviorEvaluationSerializer(evaluation.hr_evaluation)
        return Response({
            "success": True,
            "message": "HR behavioral evaluation retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update HR/Behavioral Assessment",
        request=HRBehaviorEvaluationSerializer,
        responses={200: HRBehaviorEvaluationSerializer}
    )
    def put(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        hr_eval = evaluation.hr_evaluation
        serializer = HRBehaviorEvaluationSerializer(hr_eval, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "HR/Behavioral evaluation updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class OverallEvaluationDetailView(EvaluationBaseView):
    """
    GET /api/feedback/{interview_id}/overall
    PUT /api/feedback/{interview_id}/overall
    """
    @extend_schema(
        summary="Get Overall Score Card Summary",
        responses={200: OverallEvaluationSerializer}
    )
    def get(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        serializer = OverallEvaluationSerializer(evaluation.overall_evaluation)
        return Response({
            "success": True,
            "message": "Overall evaluation retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update Overall Score Card Summary",
        request=OverallEvaluationSerializer,
        responses={200: OverallEvaluationSerializer}
    )
    def put(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        overall_eval = evaluation.overall_evaluation
        serializer = OverallEvaluationSerializer(overall_eval, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Overall evaluation updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class SuggestionsListView(EvaluationBaseView):
    """
    GET /api/feedback/{interview_id}/suggestions
    POST /api/feedback/{interview_id}/suggestions
    """
    @extend_schema(
        summary="Get Suggestions List",
        responses={200: ImprovementSuggestionSerializer(many=True)}
    )
    def get(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        serializer = ImprovementSuggestionSerializer(evaluation.suggestions.all(), many=True)
        return Response({
            "success": True,
            "message": "Suggestions fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create Improvement Suggestion",
        request=ImprovementSuggestionSerializer,
        responses={201: ImprovementSuggestionSerializer}
    )
    def post(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        data = request.data.copy()
        data['evaluation'] = evaluation.id
        
        serializer = ImprovementSuggestionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Log history
        EvaluationHistory.objects.create(
            evaluation=evaluation,
            action="Suggestion Added",
            description=f"Added improvement suggestion: {serializer.validated_data['title']}."
        )

        return Response({
            "success": True,
            "message": "Suggestion created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class SuggestionsDetailView(APIView):
    """
    PUT /api/feedback/suggestions/{id}
    DELETE /api/feedback/suggestions/{id}
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self, pk):
        suggestion = get_object_or_404(ImprovementSuggestion, pk=pk)
        self.check_object_permissions(self.request, suggestion)
        return suggestion

    @extend_schema(
        summary="Update Improvement Suggestion",
        request=ImprovementSuggestionSerializer,
        responses={200: ImprovementSuggestionSerializer}
    )
    def put(self, request, id):
        suggestion = self.get_object(id)
        serializer = ImprovementSuggestionSerializer(suggestion, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Log history
        EvaluationHistory.objects.create(
            evaluation=suggestion.evaluation,
            action="Suggestion Updated",
            description=f"Updated suggestion: {suggestion.title}."
        )

        return Response({
            "success": True,
            "message": "Suggestion updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete Improvement Suggestion",
        responses={200: OpenApiResponse(description="Deleted successfully.")}
    )
    def delete(self, request, id):
        suggestion = self.get_object(id)
        evaluation = suggestion.evaluation
        title = suggestion.title
        suggestion.delete()

        # Log history
        EvaluationHistory.objects.create(
            evaluation=evaluation,
            action="Suggestion Deleted",
            description=f"Removed suggestion: {title}."
        )

        return Response({
            "success": True,
            "message": "Suggestion deleted successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)


class ResourcesListView(EvaluationBaseView):
    """
    GET /api/feedback/{interview_id}/resources
    POST /api/feedback/{interview_id}/resources
    """
    @extend_schema(
        summary="Get Recommended Resources",
        responses={200: RecommendedResourceSerializer(many=True)}
    )
    def get(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        serializer = RecommendedResourceSerializer(evaluation.resources.all(), many=True)
        return Response({
            "success": True,
            "message": "Recommended resources fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create Recommended Resource",
        request=RecommendedResourceSerializer,
        responses={201: RecommendedResourceSerializer}
    )
    def post(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        data = request.data.copy()
        data['evaluation'] = evaluation.id

        serializer = RecommendedResourceSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Log history
        EvaluationHistory.objects.create(
            evaluation=evaluation,
            action="Resource Added",
            description=f"Added study resource recommendation: {serializer.validated_data['title']}."
        )

        return Response({
            "success": True,
            "message": "Recommended resource created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class EvaluationHistoryListView(EvaluationBaseView):
    """
    GET /api/feedback/{interview_id}/history
    """
    @extend_schema(
        summary="Get Modification History Logs",
        responses={200: EvaluationHistorySerializer(many=True)}
    )
    def get(self, request, interview_id):
        evaluation = self.get_evaluation(interview_id)
        logs = evaluation.history_logs.all().order_by('-performed_at')
        serializer = EvaluationHistorySerializer(logs, many=True)
        return Response({
            "success": True,
            "message": "Evaluation history logs retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class ExportReportView(EvaluationBaseView):
    """
    GET /api/feedback/{interview_id}/export
    Returns dummy application/pdf response. Actual generation implemented later.
    """
    @extend_schema(
        summary="Export PDF Report Card",
        description="Generates and streams pdf file response format.",
        responses={
            200: OpenApiResponse(description="PDF file output streamed.")
        }
    )
    def get(self, request, interview_id):
        # Authenticate and authorize checks
        evaluation = self.get_evaluation(interview_id)
        
        # Stream mock PDF file content
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n180\n%%EOF"
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="interview_report_{interview_id}.pdf"'
        
        # Log export history
        EvaluationHistory.objects.create(
            evaluation=evaluation,
            action="PDF Exported",
            description="PDF report downloaded by user."
        )
        
        return response
