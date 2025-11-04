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
from .utils import (
    get_cached_log_stats, get_cached_recent_anomalies, 
    get_cached_hourly_chart_data, get_optimized_filtered_logs,
    get_cached_log_distributions, get_cached_system_metrics
)
from monitoring.utils import get_system_status
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
    # Use cached statistics
    stats = get_cached_log_stats()
    
    # Get cached recent anomalies
    recent_anomalies_data = get_cached_recent_anomalies(limit=10)
    
    # Get system status (cached in monitoring utils)
    system_status = get_system_status()
    
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
        'system_status': system_status,
        'settings': settings,
    }
    
    return render(request, 'dashboard/overview.html', context)


@login_required
def log_details(request):
    """Log details page with optimized search and filtering"""
    # Get filter parameters
    host_ip = request.GET.get('host_ip')
    log_type = request.GET.get('log_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Use optimized filtering
    logs = get_optimized_filtered_logs(host_ip, log_type, date_from, date_to)
    
    # Get cached statistics
    stats = get_cached_log_stats()
    
    # Pagination with optimized query
    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_logs': stats['total_logs'],
        'error_count': stats['error_count'],
        'warning_count': stats['warning_count'],
        'info_count': stats['info_count'],
        'debug_count': stats['debug_count'],
        'host_ip': host_ip,
        'log_type': log_type,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'dashboard/log_details.html', context)


@cache_page(60)  # Cache for 1 minute
def api_dashboard_data(request):
    """API endpoint for dashboard real-time data with caching"""
    # Use cached statistics
    stats = get_cached_log_stats()
    
    # Get cached recent anomalies
    recent_anomalies_data = get_cached_recent_anomalies(limit=5)
    
    # Get cached system status
    system_status = get_system_status()
    
    return JsonResponse({
        'total_logs': stats['total_logs'],
        'total_anomalies': Anomaly.objects.count(),  # TODO: Cache this
        'error_count': stats['error_count'],
        'warning_count': stats['warning_count'],
        'info_count': stats['info_count'],
        'debug_count': stats['debug_count'],
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
