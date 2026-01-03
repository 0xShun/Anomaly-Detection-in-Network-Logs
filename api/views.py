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


@api_view(['POST', 'GET'])
@authentication_classes([APIKeyAuthentication])
@permission_classes([IsAuthenticated])
def system_status(request):
    """
    POST /api/system-status/
    
    Local network sends Kafka/Zookeeper/Consumer status updates.
    Request body:
        {
            "kafka": {"status": "running", "details": "Broker accessible"},
            "zookeeper": {"status": "running", "details": "Port 2181 open"},
            "consumer": {"status": "running", "details": "PID 12345"}
        }
    
    GET /api/system-status/
    
    Retrieve current system status for dashboard display.
    """
    from .models import LocalSystemStatus
    
    if request.method == 'POST':
        data = request.data
        
        # Get or create status record
        system_status_obj = LocalSystemStatus.get_latest()
        
        # Update Kafka status
        kafka = data.get('kafka', {})
        system_status_obj.kafka_status = kafka.get('status', 'not_applicable')
        system_status_obj.kafka_details = kafka.get('details', 'No details provided')
        
        # Update Zookeeper status
        zookeeper = data.get('zookeeper', {})
        system_status_obj.zookeeper_status = zookeeper.get('status', 'not_applicable')
        system_status_obj.zookeeper_details = zookeeper.get('details', 'No details provided')
        
        # Update Consumer status
        consumer = data.get('consumer', {})
        system_status_obj.consumer_status = consumer.get('status', 'not_applicable')
        system_status_obj.consumer_details = consumer.get('details', 'No details provided')
        
        # Determine overall status
        statuses = [system_status_obj.kafka_status, system_status_obj.zookeeper_status, system_status_obj.consumer_status]
        if all(s == 'running' for s in statuses):
            system_status_obj.overall_status = 'running'
        elif any(s == 'error' for s in statuses):
            system_status_obj.overall_status = 'error'
        elif any(s == 'stopped' for s in statuses):
            system_status_obj.overall_status = 'stopped'
        else:
            system_status_obj.overall_status = 'not_applicable'
        
        system_status_obj.save()
        
        return Response({
            'status': 'updated',
            'timestamp': system_status_obj.last_updated.isoformat(),
            'overall_status': system_status_obj.overall_status
        }, status=status.HTTP_200_OK)
    
    else:  # GET
        system_status_obj = LocalSystemStatus.get_latest()
        return Response({
            'overall': system_status_obj.overall_status,
            'kafka': {
                'status': system_status_obj.kafka_status,
                'details': system_status_obj.kafka_details
            },
            'zookeeper': {
                'status': system_status_obj.zookeeper_status,
                'details': system_status_obj.zookeeper_details
            },
            'consumer': {
                'status': system_status_obj.consumer_status,
                'details': system_status_obj.consumer_details
            },
            'last_updated': system_status_obj.last_updated.isoformat()
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([APIKeyAuthentication])
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def receive_log(request):
    """
    POST /api/logs/
    
    Receive log data from local consumer with Hybrid-BERT classification results.
    
    Request body (JSON):
        {
            "timestamp": "2026-01-04 14:35:00",
            "host_ip": "192.168.1.100",
            "log_type": "apache",
            "source": "apache",
            "log_message": "Failed password for admin from 192.168.1.100",
            "classification_class": 1,
            "classification_name": "Security Anomaly",
            "anomaly_score": 0.7696,
            "severity": "critical",
            "is_anomaly": true
        }
    
    Required fields: log_message, timestamp, classification_class, 
                     classification_name, anomaly_score, severity, is_anomaly
    Optional fields: host_ip, source, log_type
    
    Note: No authentication required for demo purposes
    """
    from dashboard.models import LogEntry, Anomaly
    from django.utils.dateparse import parse_datetime
    from datetime import datetime
    
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['log_message', 'timestamp', 'classification_class', 
                          'classification_name', 'anomaly_score', 'severity', 'is_anomaly']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return Response({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse timestamp
        timestamp_str = data.get('timestamp')
        timestamp = parse_datetime(timestamp_str)
        if not timestamp:
            # Try alternative formats
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
                except ValueError:
                    from django.utils import timezone
                    timestamp = timezone.now()
        
        # Extract classification data
        classification_class = int(data.get('classification_class'))
        classification_name = data.get('classification_name')
        anomaly_score = float(data.get('anomaly_score', 0.0))
        severity = data.get('severity', 'info')
        is_anomaly = data.get('is_anomaly', False)
        
        # Create log entry with classification data (always created for all logs)
        log_entry = LogEntry.objects.create(
            timestamp=timestamp,
            host_ip=data.get('host_ip', 'unknown'),
            log_type=data.get('log_type', 'INFO'),
            source=data.get('source', 'unknown'),
            log_message=data.get('log_message', ''),
            classification_class=classification_class,
            classification_name=classification_name,
            severity=severity,
            anomaly_score=anomaly_score
        )
        
        # Create anomaly record ONLY for Security (1) and System Failure (2)
        # All other classifications (0, 3, 4, 5, 6) are logged but not marked as anomalies
        if classification_class in [1, 2]:  # Security or System Failure
            Anomaly.objects.create(
                log_entry=log_entry,
                anomaly_score=anomaly_score,
                is_anomaly=is_anomaly,
                classification_class=classification_class,
                classification_name=classification_name,
                severity=severity,
                threshold=0.5
            )
            anomaly_created = True
        else:
            anomaly_created = False
        
        return Response({
            'status': 'success',
            'log_id': log_entry.id,
            'classification': classification_name,
            'anomaly_created': anomaly_created,
            'message': 'Log received and processed'
        }, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response({
            'status': 'error',
            'message': f'Invalid data type: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
