"""
API Views for receiving data from local network.

All endpoints require API key authentication.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Alert, SystemMetric, LogStatistic, RawModelOutput
from .serializers import (
    AlertSerializer, SystemMetricSerializer, 
    LogStatisticSerializer, RawModelOutputSerializer
)
from .authentication import APIKeyAuthentication


class AlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint for receiving anomaly alerts.
    
    POST /api/v1/alerts/
        Submit new alert from local network
    
    GET /api/v1/alerts/
        List recent alerts (for internal use)
    """
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter alerts by query parameters."""
        queryset = Alert.objects.all()
        
        # Filter by alert level
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(alert_level=level)
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by school_id
        school_id = self.request.query_params.get('school_id')
        if school_id:
            queryset = queryset.filter(school_id=school_id)
        
        return queryset.order_by('-timestamp')[:1000]  # Limit to 1000 most recent


class SystemMetricViewSet(viewsets.ModelViewSet):
    """
    API endpoint for receiving system metrics.
    
    POST /api/v1/metrics/
        Submit system metrics from local network
    
    GET /api/v1/metrics/
        List recent metrics
    """
    queryset = SystemMetric.objects.all()
    serializer_class = SystemMetricSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter metrics by query parameters."""
        queryset = SystemMetric.objects.all()
        
        metric_type = self.request.query_params.get('type')
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        
        school_id = self.request.query_params.get('school_id')
        if school_id:
            queryset = queryset.filter(school_id=school_id)
        
        return queryset.order_by('-timestamp')[:1000]


class LogStatisticViewSet(viewsets.ModelViewSet):
    """
    API endpoint for receiving log statistics.
    
    POST /api/v1/statistics/
        Submit log processing statistics
    
    GET /api/v1/statistics/
        List recent statistics
    """
    queryset = LogStatistic.objects.all()
    serializer_class = LogStatisticSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter statistics by query parameters."""
        queryset = LogStatistic.objects.all()
        
        school_id = self.request.query_params.get('school_id')
        if school_id:
            queryset = queryset.filter(school_id=school_id)
        
        return queryset.order_by('-timestamp')[:500]


class RawModelOutputViewSet(viewsets.ModelViewSet):
    """
    API endpoint for receiving raw model outputs.
    
    POST /api/v1/raw-outputs/
        Submit raw model inference outputs
    
    GET /api/v1/raw-outputs/
        List recent raw outputs
    """
    queryset = RawModelOutput.objects.all()
    serializer_class = RawModelOutputSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter raw outputs by query parameters."""
        queryset = RawModelOutput.objects.all()
        
        school_id = self.request.query_params.get('school_id')
        if school_id:
            queryset = queryset.filter(school_id=school_id)
        
        model_name = self.request.query_params.get('model')
        if model_name:
            queryset = queryset.filter(model_name=model_name)
        
        # Filter by anomaly status
        is_anomaly = self.request.query_params.get('is_anomaly')
        if is_anomaly is not None:
            queryset = queryset.filter(is_anomaly=is_anomaly.lower() == 'true')
        
        return queryset.order_by('-timestamp')[:500]


@api_view(['GET'])
@authentication_classes([APIKeyAuthentication])
@permission_classes([IsAuthenticated])
def api_status(request):
    """
    Check API status and connectivity.
    
    GET /api/v1/status
    
    Returns basic API health information.
    """
    return Response({
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0',
        'endpoints': {
            'alerts': '/api/v1/alerts/',
            'metrics': '/api/v1/metrics/',
            'statistics': '/api/v1/statistics/',
            'raw_outputs': '/api/v1/raw-outputs/',
            'health': '/api/v1/health/',
        }
    })


@api_view(['POST'])
@authentication_classes([APIKeyAuthentication])
@permission_classes([IsAuthenticated])
def health_check(request):
    """
    Health check endpoint for local network monitoring.
    
    POST /api/v1/health
    
    Local network can send periodic health checks.
    Request body:
        {
            "school_id": "university_main",
            "status": "running",
            "last_analysis": "2025-11-04T10:30:00Z",
            "components": {"parser": "ok", "model": "ok"}
        }
    """
    data = request.data
    
    # Could store health check data in a model if needed
    # For now, just acknowledge receipt
    
    return Response({
        'status': 'received',
        'timestamp': timezone.now().isoformat(),
        'message': 'Health check recorded'
    }, status=status.HTTP_200_OK)
