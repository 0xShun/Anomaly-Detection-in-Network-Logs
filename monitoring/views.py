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
    from api.models import LocalSystemStatus
    from datetime import timedelta
    import psutil
    import os
    
    # Get system status from API model (updated by local network via API)
    system_status_obj = LocalSystemStatus.get_latest()
    system_status = {
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
    }
    
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
    
    # Get system status from database (now refreshed with live data)
    db_system_status = SystemStatusModel.objects.all()
    
    # Get actual system health metrics using psutil (no caching - fresh reads)
    try:
        # Memory usage - read directly from /proc/meminfo on Linux
        memory = psutil.virtual_memory()
        memory_percent = round(memory.percent, 1)
        memory_used_gb = round(memory.used / (1024**3), 2)
        memory_total_gb = round(memory.total / (1024**3), 2)
        
        # Memory status thresholds
        if memory_percent < 75:
            memory_status = 'Normal'
            memory_badge = 'bg-success'
        elif memory_percent < 85:
            memory_status = 'Warning'
            memory_badge = 'bg-warning'
        else:
            memory_status = 'Critical'
            memory_badge = 'bg-danger'
        
        # Disk usage - read directly from filesystem stats
        disk = psutil.disk_usage('/')
        disk_percent = round(disk.percent, 1)
        disk_used_gb = round(disk.used / (1024**3), 2)
        disk_total_gb = round(disk.total / (1024**3), 2)
        
        # Disk status thresholds
        if disk_percent < 75:
            disk_status = 'Healthy'
            disk_badge = 'bg-success'
        elif disk_percent < 85:
            disk_status = 'Warning'
            disk_badge = 'bg-warning'
        else:
            disk_status = 'Critical'
            disk_badge = 'bg-danger'
        
        # Database connection - test with actual query
        db_status = 'Healthy'
        db_badge = 'bg-success'
        try:
            log_count = LogEntry.objects.count()
            db_detail = f'{log_count} total log entries'
        except Exception as db_error:
            db_status = 'Error'
            db_badge = 'bg-danger'
            db_detail = f'Connection failed: {str(db_error)[:50]}'
            
    except ImportError:
        # psutil not installed
        memory_percent = 0
        memory_used_gb = 0
        memory_total_gb = 0
        memory_status = 'Unknown'
        memory_badge = 'bg-secondary'
        disk_percent = 0
        disk_used_gb = 0
        disk_total_gb = 0
        disk_status = 'Unknown'
        disk_badge = 'bg-secondary'
        db_status = 'Unknown'
        db_badge = 'bg-secondary'
        db_detail = 'psutil not installed'
    except Exception as e:
        # Fallback for other errors
        memory_percent = 0
        memory_used_gb = 0
        memory_total_gb = 0
        memory_status = 'Error'
        memory_badge = 'bg-danger'
        disk_percent = 0
        disk_used_gb = 0
        disk_total_gb = 0
        disk_status = 'Error'
        disk_badge = 'bg-danger'
        db_status = 'Error'
        db_badge = 'bg-danger'
        db_detail = f'Error: {str(e)[:50]}'
    
    # Get recent activity from actual system events
    recent_activity = []
    
    # Recent anomaly detection
    recent_anomaly = Anomaly.objects.order_by('-detected_at').first()
    if recent_anomaly:
        time_diff = (now - recent_anomaly.detected_at).total_seconds()
        if time_diff < 3600:  # Last hour
            minutes = int(time_diff / 60)
            recent_activity.append({
                'icon': 'exclamation-triangle',
                'icon_color': 'warning',
                'title': 'Anomaly Detected',
                'description': f'High anomaly score: {recent_anomaly.anomaly_score:.3f}',
                'time': f'{minutes} minute{"s" if minutes != 1 else ""} ago'
            })
    
    # Recent log ingestion
    recent_log = LogEntry.objects.order_by('-created_at').first()
    if recent_log:
        time_diff = (now - recent_log.created_at).total_seconds()
        if time_diff < 3600:
            minutes = int(time_diff / 60)
            recent_activity.append({
                'icon': 'file-alt',
                'icon_color': 'info',
                'title': 'Log Ingested',
                'description': f'{logs_last_hour} logs processed in last hour',
                'time': f'{minutes} minute{"s" if minutes != 1 else ""} ago'
            })
    
    # System status checks
    for status in db_system_status[:3]:  # Last 3 status checks
        if status.last_check:
            time_diff = (now - status.last_check).total_seconds()
            if time_diff < 3600:
                minutes = int(time_diff / 60)
                icon_color = 'success' if status.status == 'running' else 'danger'
                recent_activity.append({
                    'icon': 'shield-alt',
                    'icon_color': icon_color,
                    'title': f'{status.service_name.title()} Status Check',
                    'description': f'Status: {status.status}',
                    'time': f'{minutes} minute{"s" if minutes != 1 else ""} ago'
                })
    
    # If no activity, show system start message
    if not recent_activity:
        recent_activity.append({
            'icon': 'check',
            'icon_color': 'success',
            'title': 'System Operational',
            'description': 'All services running normally',
            'time': 'Now'
        })
    
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
        'health_metrics': {
            'database': {
                'status': db_status,
                'badge': db_badge,
                'detail': db_detail
            },
            'memory': {
                'percent': memory_percent,
                'used_gb': memory_used_gb,
                'total_gb': memory_total_gb,
                'status': memory_status,
                'badge': memory_badge
            },
            'disk': {
                'percent': disk_percent,
                'used_gb': disk_used_gb,
                'total_gb': disk_total_gb,
                'status': disk_status,
                'badge': disk_badge
            }
        },
        'recent_activity': recent_activity[:5],  # Show max 5 recent activities
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
