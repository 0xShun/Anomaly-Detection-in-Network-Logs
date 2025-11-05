from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from datetime import datetime, timedelta
from .models import LogEntry, Anomaly, SystemStatus, PlatformSettings
from api.models import Alert, SystemMetric, LogStatistic  # Import real API models
from .utils import (
    get_cached_log_stats, get_cached_recent_anomalies, 
    get_cached_hourly_chart_data, get_optimized_filtered_logs,
    get_cached_log_distributions, get_cached_system_metrics
)
import json
import threading
import subprocess
import sys
import os
import time
from django.conf import settings
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseBadRequest


@login_required
def dashboard_overview(request):
    """Main dashboard overview page with optimized queries"""
    # Get user preferences
    from authentication.models import UserPreferences
    user_preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    
    # Use cached statistics
    stats = get_cached_log_stats()
    
    # Get cached recent anomalies
    recent_anomalies_data = get_cached_recent_anomalies(limit=10)
    
    # Get system status from API model (updated by local network)
    from api.models import LocalSystemStatus
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
    
    # Get platform settings (cache this too)
    settings_cache_key = 'platform_settings'
    settings = cache.get(settings_cache_key)
    if settings is None:
        try:
            settings = PlatformSettings.objects.first()
            if not settings:
                settings = PlatformSettings.objects.create()
        except:
            settings = PlatformSettings.objects.create()
        cache.set(settings_cache_key, settings, 300)  # Cache for 5 minutes
    
    context = {
        'total_logs': stats['total_logs'],
        'total_anomalies': Anomaly.objects.count(),  # TODO: Cache this too
        'error_count': stats['error_count'],
        'warning_count': stats['warning_count'],
        'info_count': stats['info_count'],
        'debug_count': stats['debug_count'],
        'recent_anomalies': recent_anomalies_data,
        'user_preferences': user_preferences,
        'system_status': system_status,
        'settings': settings,
    }
    
    return render(request, 'dashboard/overview.html', context)


@login_required
def anomaly_feed_partial(request):
    """Return just the anomaly feed table rows as HTML"""
    # Get recent anomalies (same as dashboard_overview)
    recent_anomalies_data = get_cached_recent_anomalies(limit=50)
    
    context = {
        'recent_anomalies': recent_anomalies_data,
    }
    
    return render(request, 'dashboard/partials/anomaly_feed_rows.html', context)


@login_required
def dashboard_stats(request):
    """Return just the stats (total logs, anomalies) as JSON"""
    stats = get_cached_log_stats()
    
    return JsonResponse({
        'total_logs': stats['total_logs'],
        'total_anomalies': Anomaly.objects.count(),
    })


@login_required
def log_details(request):
    """Log details page with optimized search and filtering"""
    # Get user preferences for items per page
    from authentication.models import UserPreferences
    user_preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    items_per_page = user_preferences.items_per_page
    
    # Get filter parameters
    host_ip = request.GET.get('host_ip')
    log_type = request.GET.get('log_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Use optimized filtering
    logs = get_optimized_filtered_logs(host_ip, log_type, date_from, date_to)
    
    # Calculate statistics based on filtered logs (not global stats)
    # This ensures stats match what user sees
    from django.db.models import Case, When, IntegerField
    
    filtered_stats = logs.aggregate(
        total_logs=Count('id'),
        error_count=Count(Case(
            When(log_type='error', then=1),
            output_field=IntegerField()
        )),
        warning_count=Count(Case(
            When(log_type='warning', then=1),
            output_field=IntegerField()
        )),
        info_count=Count(Case(
            When(log_type='info', then=1),
            output_field=IntegerField()
        )),
        debug_count=Count(Case(
            When(log_type='debug', then=1),
            output_field=IntegerField()
        ))
    )
    
    # Pagination with user's preferred items per page
    paginator = Paginator(logs, items_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_logs': filtered_stats['total_logs'],
        'error_count': filtered_stats['error_count'],
        'warning_count': filtered_stats['warning_count'],
        'info_count': filtered_stats['info_count'],
        'debug_count': filtered_stats['debug_count'],
        'host_ip': host_ip,
        'log_type': log_type,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'dashboard/log_details.html', context)


def api_dashboard_data(request):
    """API endpoint for dashboard real-time data - reads from actual LogEntry and Anomaly tables"""
    try:
        from .utils import get_system_status
        
        # Get total logs count
        total_logs = LogEntry.objects.count()
        
        # Get total anomalies count
        total_anomalies = Anomaly.objects.count()
        
        # Get log type counts
        error_count = LogEntry.objects.filter(log_type='ERROR').count()
        warning_count = LogEntry.objects.filter(log_type='WARNING').count()
        info_count = LogEntry.objects.filter(log_type='INFO').count()
        debug_count = LogEntry.objects.filter(log_type='DEBUG').count()
    except Exception as e:
        # Return error details for debugging
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'message': 'Error fetching dashboard data'
        }, status=500)
    
    # Get recent anomalies (most recent 50)
    try:
        recent_anomalies = Anomaly.objects.select_related('log_entry').order_by('-detected_at')[:50]
    except Exception as e:
        recent_anomalies = []
    
    recent_anomalies_data = []
    for anomaly in recent_anomalies:
        try:
            # Skip if log_entry is None (orphaned anomaly)
            if not anomaly.log_entry:
                continue
                
            # Determine confidence level based on anomaly score
            anomaly_score = float(anomaly.anomaly_score)
            if anomaly_score >= 0.9:
                confidence = 'Critical'
            elif anomaly_score >= 0.7:
                confidence = 'High Confidence'
            elif anomaly_score >= 0.5:
                confidence = 'Medium Confidence'
            elif anomaly_score >= 0.3:
                confidence = 'Low Confidence'
            else:
                confidence = 'Suspicious'
            
            recent_anomalies_data.append({
                'id': anomaly.id,
                'timestamp': anomaly.log_entry.timestamp.strftime('%m/%d/%Y, %I:%M:%S %p'),
                'host_ip': anomaly.log_entry.host_ip,
                'log_message': anomaly.log_entry.log_message,
                'anomaly_score': anomaly_score,
                'status': confidence,
            })
        except Exception as e:
            # Skip this anomaly if there's any error
            continue
    
    # Get system status from API model (updated by local network)
    from api.models import LocalSystemStatus
    try:
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
    except Exception as e:
        # If no status available, return default values
        system_status = {
            'overall': 'not_applicable',
            'kafka': {
                'status': 'unknown',
                'details': 'No status data available'
            },
            'zookeeper': {
                'status': 'unknown',
                'details': 'No status data available'
            },
            'consumer': {
                'status': 'unknown',
                'details': 'No status data available'
            },
        }
    
    return JsonResponse({
        'total_logs': total_logs,
        'total_anomalies': total_anomalies,
        'error_count': error_count,
        'warning_count': warning_count,
        'info_count': info_count,
        'debug_count': debug_count,
        'recent_anomalies': recent_anomalies_data,
        'system_status': system_status,
        'timestamp': timezone.now().isoformat(),
    })


def api_anomaly_feed(request):
    """API endpoint for real-time anomaly feed"""
    # Get recent anomalies with pagination
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 10))
    
    anomalies = Anomaly.objects.select_related('log_entry').order_by('-detected_at')
    paginator = Paginator(anomalies, per_page)
    
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    anomalies_data = []
    for anomaly in page_obj:
        anomalies_data.append({
            'id': anomaly.id,
            'timestamp': anomaly.log_entry.timestamp.isoformat(),
            'host_ip': anomaly.log_entry.host_ip,
            'log_message': anomaly.log_entry.log_message,
            'anomaly_score': anomaly.anomaly_score,
            'threshold': anomaly.threshold,
        })
    
    return JsonResponse({
        'anomalies': anomalies_data,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
    })


@login_required
def api_log_detail(request, log_id):
    """API endpoint to get detailed information about a specific log entry"""
    try:
        log = LogEntry.objects.get(id=log_id)
        
        # Check if this log has any anomalies
        anomalies = log.anomalies.all()
        anomaly_data = []
        for anomaly in anomalies:
            anomaly_data.append({
                'id': anomaly.id,
                'score': float(anomaly.anomaly_score),
                'threshold': float(anomaly.threshold),
                'is_anomaly': anomaly.is_anomaly,
                'acknowledged': anomaly.acknowledged,
                'detected_at': anomaly.detected_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        data = {
            'success': True,
            'log': {
                'id': log.id,
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'host_ip': log.host_ip,
                'log_type': log.log_type or 'unknown',
                'source': log.source or '-',
                'log_message': log.log_message,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            },
            'anomalies': anomaly_data,
        }
        return JsonResponse(data)
    except LogEntry.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Log entry not found'
        }, status=404)


# Optimized API endpoints for Streamlit
@cache_page(300)  # Cache for 5 minutes
def api_streamlit_chart_data(request):
    """API endpoint for Streamlit chart data with database aggregation"""
    # Get time range (default: last 24 hours)
    hours = int(request.GET.get('hours', 24))
    
    # Get cached hourly data
    hourly_data = get_cached_hourly_chart_data(hours)
    
    # Get cached distributions
    distributions = get_cached_log_distributions(hours)
    
    return JsonResponse({
        'hourly_data': [
            {
                'hour': item['hour'].strftime('%Y-%m-%d %H:00'),
                'total_logs': item['total_logs'],
                'error_logs': item['error_logs'],
                'warning_logs': item['warning_logs'],
                'info_logs': item['info_logs'],
                'debug_logs': item['debug_logs'],
            } for item in hourly_data
        ],
        'log_type_distribution': distributions['log_type_distribution'],
        'host_distribution': distributions['host_distribution'],
        'source_distribution': distributions['source_distribution'],
        'time_range': f'Last {hours} hours'
    })


def api_streamlit_anomaly_data(request):
    """API endpoint for Streamlit anomaly analysis"""
    # Get anomalies with their log details
    anomalies = Anomaly.objects.select_related('log_entry').order_by('-detected_at')
    
    anomaly_data = []
    for anomaly in anomalies:
        anomaly_data.append({
            'id': anomaly.id,
            'timestamp': anomaly.log_entry.timestamp.isoformat(),
            'host_ip': anomaly.log_entry.host_ip,
            'log_type': anomaly.log_entry.log_type,
            'source': anomaly.log_entry.source,
            'log_message': anomaly.log_entry.log_message,
            'anomaly_score': anomaly.anomaly_score,
            'threshold': anomaly.threshold,
            'is_anomaly': anomaly.is_anomaly
        })
    
    # Get anomaly score distribution
    score_ranges = [
        {'range': '0.5-0.6', 'count': anomalies.filter(anomaly_score__range=(0.5, 0.6)).count()},
        {'range': '0.6-0.7', 'count': anomalies.filter(anomaly_score__range=(0.6, 0.7)).count()},
        {'range': '0.7-0.8', 'count': anomalies.filter(anomaly_score__range=(0.7, 0.8)).count()},
        {'range': '0.8-0.9', 'count': anomalies.filter(anomaly_score__range=(0.8, 0.9)).count()},
        {'range': '0.9-1.0', 'count': anomalies.filter(anomaly_score__range=(0.9, 1.0)).count()},
    ]
    
    # Get anomalies by log type
    anomalies_by_type = list(anomalies.values('log_entry__log_type').annotate(count=Count('id')))
    
    return JsonResponse({
        'anomalies': anomaly_data,
        'score_distribution': score_ranges,
        'anomalies_by_type': anomalies_by_type,
        'total_anomalies': anomalies.count()
    })


@cache_page(180)  # Cache for 3 minutes
def api_streamlit_system_metrics(request):
    """API endpoint for Streamlit system metrics with caching"""
    # Get cached system status
    system_status = get_system_status()
    
    # Get cached metrics
    metrics = get_cached_system_metrics()
    
    return JsonResponse({
        'system_status': system_status,
        'metrics': metrics,
        'last_updated': timezone.now().isoformat()
    })


@login_required
@require_POST
def run_pipeline(request):
    """Trigger a background run that populates sample data and runs performance analysis.

    This starts a background thread which runs two management commands sequentially:
      1. populate_sample_data --clear
      2. performance --analyze

    The background runner writes status and output to files under BASE_DIR / 'logs'.
    """
    base_dir = settings.BASE_DIR
    logs_dir = os.path.join(base_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    status_path = os.path.join(logs_dir, 'pipeline_status.json')
    output_path = os.path.join(logs_dir, 'pipeline_output.log')

    # Prevent multiple concurrent runs
    try:
        if os.path.exists(status_path):
            with open(status_path, 'r') as f:
                st = json.load(f)
                if st.get('status') == 'running':
                    return JsonResponse({'status': 'already_running'}, status=409)
    except Exception:
        # If status read fails, continue and overwrite
        pass

    def _runner():
        start = time.time()
        status = {'status': 'running', 'started_at': time.time(), 'pid': None}
        with open(status_path, 'w') as f:
            json.dump(status, f)

        # Open output file and append outputs
        with open(output_path, 'a') as out_f:
            try:
                # 1) populate_sample_data --clear
                cmd1 = [sys.executable, str(base_dir / 'manage.py'), 'populate_sample_data', '--clear']
                out_f.write(f"\n=== Running: {' '.join(cmd1)} ===\n")
                out_f.flush()
                proc1 = subprocess.run(cmd1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                out_f.write(proc1.stdout)
                out_f.flush()

                # 2) performance --analyze
                cmd2 = [sys.executable, str(base_dir / 'manage.py'), 'performance', '--analyze']
                out_f.write(f"\n=== Running: {' '.join(cmd2)} ===\n")
                out_f.flush()
                proc2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                out_f.write(proc2.stdout)
                out_f.flush()

                duration = time.time() - start
                final_status = {
                    'status': 'completed',
                    'completed_at': time.time(),
                    'duration_seconds': duration,
                    'last_return_codes': [proc1.returncode, proc2.returncode]
                }
                with open(status_path, 'w') as f:
                    json.dump(final_status, f)

            except Exception as e:
                out_f.write(f"\n=== Runner exception: {e} ===\n")
                with open(status_path, 'w') as f:
                    json.dump({'status': 'failed', 'error': str(e), 'timestamp': time.time()}, f)

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()

    return JsonResponse({'status': 'started'})


@login_required
def pipeline_status(request):
    """Return the current pipeline status and last few lines of output."""
    base_dir = settings.BASE_DIR
    logs_dir = os.path.join(base_dir, 'logs')
    status_path = os.path.join(logs_dir, 'pipeline_status.json')
    output_path = os.path.join(logs_dir, 'pipeline_output.log')

    status = {'status': 'not_started'}
    if os.path.exists(status_path):
        try:
            with open(status_path, 'r') as f:
                status = json.load(f)
        except Exception:
            status = {'status': 'unknown'}

    # Return last 2000 characters of output for quick preview
    output_preview = ''
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                # Read last ~2000 chars
                to_read = 2000
                f.seek(max(size - to_read, 0))
                output_preview = f.read()
        except Exception:
            output_preview = ''

    return JsonResponse({'status': status, 'output_preview': output_preview})


@login_required
def help_page(request):
    """Display the help and user guide page."""
    return render(request, 'dashboard/help.html')
