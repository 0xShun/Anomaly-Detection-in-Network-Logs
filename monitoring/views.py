from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .utils import get_system_status, check_kafka_status, check_zookeeper_status, check_consumer_status
from dashboard.models import SystemStatus as SystemStatusModel
import json


@login_required
def system_monitoring(request):
    """System monitoring page"""
    from dashboard.models import LogEntry, Anomaly
    from datetime import timedelta
    
    # Get current system status
    system_status = get_system_status()
    
    # Get historical status data
    status_history = SystemStatusModel.objects.order_by('-last_check')[:20]
    
    # Calculate performance metrics
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)
    
    # Logs per hour
    logs_last_hour = LogEntry.objects.filter(timestamp__gte=one_hour_ago).count()
    logs_per_hour = logs_last_hour
    
    # Anomalies per hour
    anomalies_last_hour = Anomaly.objects.filter(detected_at__gte=one_hour_ago).count()
    anomalies_per_hour = anomalies_last_hour
    
    # Get system status from database
    db_system_status = SystemStatusModel.objects.all()
    
    context = {
        'system_status': {
            'overall': system_status.get('overall', 'unknown'),
            'services': [
                {
                    'name': status.service_name,
                    'status': status.status,
                    'details': status.details
                }
                for status in db_system_status
            ]
        },
        'status_history': status_history,
        'logs_per_hour': logs_per_hour,
        'anomalies_per_hour': anomalies_per_hour,
    }
    
    return render(request, 'monitoring/system_monitoring.html', context)


@login_required
def api_system_status(request):
    """API endpoint for system status"""
    # Check all services
    kafka_status = check_kafka_status()
    zookeeper_status = check_zookeeper_status()
    consumer_status = check_consumer_status()
    
    # Update database
    SystemStatusModel.objects.update_or_create(
        service_name='kafka',
        defaults={
            'status': kafka_status['status'],
            'details': kafka_status.get('details', '')
        }
    )
    
    SystemStatusModel.objects.update_or_create(
        service_name='zookeeper',
        defaults={
            'status': zookeeper_status['status'],
            'details': zookeeper_status.get('details', '')
        }
    )
    
    SystemStatusModel.objects.update_or_create(
        service_name='consumer',
        defaults={
            'status': consumer_status['status'],
            'details': consumer_status.get('details', '')
        }
    )
    
    return JsonResponse({
        'kafka': kafka_status,
        'zookeeper': zookeeper_status,
        'consumer': consumer_status,
        'timestamp': timezone.now().isoformat(),
    })


@login_required
def api_log_ingestion_rate(request):
    """API endpoint for log ingestion rate"""
    from dashboard.models import LogEntry
    from datetime import datetime, timedelta
    
    # Calculate logs per second for the last minute
    now = timezone.now()
    one_minute_ago = now - timedelta(minutes=1)
    
    recent_logs = LogEntry.objects.filter(timestamp__gte=one_minute_ago).count()
    logs_per_second = recent_logs / 60.0
    
    return JsonResponse({
        'logs_per_second': round(logs_per_second, 2),
        'logs_last_minute': recent_logs,
        'timestamp': now.isoformat(),
    })
