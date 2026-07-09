from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import (
    AIProvider,
    AIModel,
    AIRequestLog,
    AIConfiguration,
    AIUsageStatistics
)
from .permissions import IsAdminOrReadOnly, IsAdminUserOnly
from .serializers import (
    AIProviderSerializer,
    AIModelSerializer,
    AIRequestLogSerializer,
    AIConfigurationSerializer,
    AIUsageStatisticsSerializer
)
from chatbot.pagination import PrepAIPagination

class AIProviderViewSet(viewsets.ModelViewSet):
    """
    GET /api/ai/providers
    POST /api/ai/providers
    PUT /api/ai/providers/{id}
    DELETE /api/ai/providers/{id}
    (Admins can CRUD, authenticated users can read).
    """
    queryset = AIProvider.objects.all()
    serializer_class = AIProviderSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'id'


class AIModelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/ai/models
    GET /api/ai/models/{id}
    """
    queryset = AIModel.objects.all()
    serializer_class = AIModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'


class AIHealthCheckView(APIView):
    """
    GET /api/ai/health
    Returns health status of the AI Core components.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get AI Health Check Status",
        responses={200: OpenApiResponse(description="Health check state dict")}
    )
    def get(self, request):
        # Scan active model availability
        ollama_active = AIProvider.objects.filter(provider_name='Ollama', is_active=True).exists()
        gemini_active = AIProvider.objects.filter(provider_name='Gemini', is_active=True).exists()

        overall_health = "Healthy" if (ollama_active or gemini_active) else "Degraded"

        return Response({
            "success": True,
            "message": "AI health status fetched.",
            "data": {
                "status": overall_health,
                "components": {
                    "ollama_status": "Available" if ollama_active else "Unavailable",
                    "qdrant_status": "Mock Integrated",
                    "whisper_availability": "Ready",
                    "embedding_model_availability": "Ready"
                }
            }
        }, status=status.HTTP_200_OK)


class AIConfigurationView(APIView):
    """
    GET /api/ai/config
    PUT /api/ai/config
    (Admin only dynamic settings config).
    """
    permission_classes = [IsAdminUserOnly]

    @extend_schema(
        summary="Get AI Dynamic Config Options",
        responses={200: AIConfigurationSerializer(many=True)}
    )
    def get(self, request):
        configs = AIConfiguration.objects.all()
        serializer = AIConfigurationSerializer(configs, many=True)
        return Response({
            "success": True,
            "message": "AI configurations retrieved.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create or Update AI Configuration",
        request=AIConfigurationSerializer,
        responses={200: AIConfigurationSerializer}
    )
    def put(self, request):
        key = request.data.get('key')
        value = request.data.get('value')
        if not key or not value:
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": {"detail": "key and value are required parameters."}
            }, status=status.HTTP_400_BAD_REQUEST)

        config_obj, created = AIConfiguration.objects.get_or_create(key=key)
        config_obj.value = value
        config_obj.description = request.data.get('description', config_obj.description)
        config_obj.is_active = request.data.get('is_active', config_obj.is_active)
        config_obj.save()

        serializer = AIConfigurationSerializer(config_obj)
        return Response({
            "success": True,
            "message": "AI configuration updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class AIUsageStatisticsView(APIView):
    """
    GET /api/ai/statistics
    Returns candidate's individual stats, error rates, and average latency.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Candidate AI Usage Stats",
        responses={200: AIUsageStatisticsSerializer}
    )
    def get(self, request):
        stats, created = AIUsageStatistics.objects.get_or_create(user=request.user)
        
        # Calculate error rate from request logs
        logs = AIRequestLog.objects.filter(user=request.user)
        total_logs = logs.count()
        failed_logs = logs.filter(request_status='Failed').count()
        error_rate = (failed_logs / total_logs) * 100 if total_logs > 0 else 0.0

        # Estimate mock tokens
        total_tokens = sum(log.token_usage for log in logs)

        serializer = AIUsageStatisticsSerializer(stats)
        data = serializer.data
        # Inject computed metrics
        data["error_rate"] = round(error_rate, 2)
        data["estimated_token_usage"] = total_tokens
        
        return Response({
            "success": True,
            "message": "AI usage statistics retrieved.",
            "data": data
        }, status=status.HTTP_200_OK)


class AIRequestLogListView(generics.ListAPIView):
    """
    GET /api/ai/logs
    Lists AI requests audit logs. Restricted to Admins.
    """
    serializer_class = AIRequestLogSerializer
    permission_classes = [IsAdminUserOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['request_status', 'request_type', 'module_name']
    search_fields = ['provider', 'model', 'user__email', 'error_message']
    pagination_class = PrepAIPagination

    def get_queryset(self):
        return AIRequestLog.objects.select_related('user').all()
