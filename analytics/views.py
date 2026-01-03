from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from dashboard.models import LogEntry, Anomaly
import json
from django.conf import settings


@login_required
def analytics_dashboard(request):
    """Analytics dashboard with charts"""
    # Get date range for analytics
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)  # Last 7 days
    
    # Calculate key metrics
    total_logs = LogEntry.objects.count()
    total_anomalies = Anomaly.objects.count()
    
    # Calculate anomaly rate
    anomaly_rate = 0
    if total_logs > 0:
        anomaly_rate = round((total_anomalies / total_logs) * 100, 1)
    
    # Calculate average response time
    # Based on time difference between log creation and anomaly detection
    recent_anomalies = Anomaly.objects.filter(
        detected_at__range=(start_date, end_date)
    ).select_related('log_entry')[:100]
    
    if recent_anomalies.exists():
        total_time = 0
        count = 0
        for anomaly in recent_anomalies:
            time_diff = (anomaly.detected_at - anomaly.log_entry.created_at).total_seconds() * 1000
            if time_diff >= 0:  # Only count positive time differences
                total_time += time_diff
                count += 1
        
        avg_response_time = round(total_time / count) if count > 0 else 0
    else:
        avg_response_time = 0
    
    # Get anomaly data for charts
    anomalies_by_date = Anomaly.objects.filter(
        detected_at__range=(start_date, end_date)
    ).extra(
        select={'date': 'date(detected_at)'}
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Get anomalies by source
    anomalies_by_source = LogEntry.objects.filter(
        anomalies__isnull=False
    ).values('host_ip').annotate(
        anomaly_count=Count('anomalies')
    ).order_by('-anomaly_count')[:10]
    
    # Get anomaly categories (if available)
    anomaly_categories = Anomaly.objects.values('log_entry__log_type').annotate(
        count=Count('id')
    ).exclude(log_entry__log_type='').order_by('-count')[:10]
    
    # Get anomaly score distribution
    score_ranges = [
        (0.5, 0.6),
        (0.6, 0.7),
        (0.7, 0.8),
        (0.8, 0.9),
        (0.9, 1.0)
    ]
    
    score_distribution = []
    max_count = 0
    for min_score, max_score in score_ranges:
        count = Anomaly.objects.filter(
            anomaly_score__gte=min_score,
            anomaly_score__lt=max_score
        ).count()
        if count > max_count:
            max_count = count
        score_distribution.append({
            'label': f"{min_score} - {max_score}",
            'count': count,
            'min': min_score,
            'max': max_score
        })
    
    # Calculate percentage widths for progress bars
    for item in score_distribution:
        if max_count > 0:
            item['percentage'] = int((item['count'] / max_count) * 100)
        else:
            item['percentage'] = 0
    
    # Get top anomaly sources with actual data
    top_sources = LogEntry.objects.filter(
        anomalies__isnull=False
    ).values('host_ip', 'log_type').annotate(
        anomaly_count=Count('anomalies')
    ).order_by('-anomaly_count')[:5]
    
    # Calculate max for progress bar scaling
    max_anomaly_count = 0
    for source in top_sources:
        if source['anomaly_count'] > max_anomaly_count:
            max_anomaly_count = source['anomaly_count']
    
    # Add percentage to each source
    top_sources_list = []
    for source in top_sources:
        if max_anomaly_count > 0:
            percentage = int((source['anomaly_count'] / max_anomaly_count) * 100)
        else:
            percentage = 0
        top_sources_list.append({
            'host_ip': source['host_ip'],
            'log_type': source['log_type'] or 'unknown',
            'anomaly_count': source['anomaly_count'],
            'percentage': percentage
        })
    
    context = {
        'total_logs': total_logs,
        'total_anomalies': total_anomalies,
        'anomaly_rate': anomaly_rate,
        'avg_response_time': avg_response_time,
        'anomalies_by_date': list(anomalies_by_date),
        'anomalies_by_source': list(anomalies_by_source),
        'anomaly_categories': list(anomaly_categories),
        'score_distribution': score_distribution,
        'top_sources': top_sources_list,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def api_chart_data(request):
    """API endpoint for chart data"""
    chart_type = request.GET.get('type', 'line')
    
    if chart_type == 'line':
        # Log volume over time grouped by minute, stacked by classification
        # Get all logs in database (entire time period)
        from django.db.models.functions import TruncMinute
        
        data = LogEntry.objects.exclude(
            classification_class__isnull=True
        ).annotate(
            minute=TruncMinute('timestamp')
        ).values('minute', 'classification_class').annotate(
            count=Count('id')
        ).order_by('minute', 'classification_class')
        
        # Organize data by minute and classification
        result_data = {}
        for item in data:
            minute_str = item['minute'].strftime('%Y-%m-%d %H:%M')
            class_num = item['classification_class']
            
            if minute_str not in result_data:
                result_data[minute_str] = {
                    'minute': minute_str,
                    'class_0': 0,  # Normal
                    'class_1': 0,  # Security
                    'class_2': 0,  # System Failure
                    'class_3': 0,  # Performance
                    'class_4': 0,  # Network
                    'class_5': 0,  # Config
                    'class_6': 0,  # Hardware
                }
            
            result_data[minute_str][f'class_{class_num}'] = item['count']
        
        # Convert to list sorted by minute
        sorted_data = sorted(result_data.values(), key=lambda x: x['minute'])
        
        return JsonResponse({
            'type': 'line',
            'data': sorted_data,
            'title': 'Log Volume Over Time (By Minute)'
        })
    
    elif chart_type == 'bar':
        # Anomalies by source
        from datetime import timedelta
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        
        data = LogEntry.objects.filter(
            anomalies__isnull=False,
            timestamp__range=(start_date, end_date)
        ).values('host_ip').annotate(
            count=Count('anomalies')
        ).order_by('-count')[:10]
        
        return JsonResponse({
            'type': 'bar',
            'data': list(data),
            'x_axis': 'host_ip',
            'y_axis': 'count',
            'title': f'Anomalies by Source (Last 7 days)'
        })
    
    elif chart_type == 'pie':
        # Classification Distribution (ALL logs in database)
        class_names = {
            0: 'Normal',
            1: 'Security Anomaly',
            2: 'System Failure',
            3: 'Performance Issue',
            4: 'Network Anomaly',
            5: 'Config Error',
            6: 'Hardware Issue'
        }
        
        data = LogEntry.objects.exclude(
            classification_class__isnull=True
        ).values('classification_class').annotate(
            count=Count('id')
        ).order_by('classification_class')
        
        # Add class names to data
        result_data = []
        for item in data:
            class_num = item['classification_class']
            result_data.append({
                'classification_class': class_num,
                'classification_name': class_names.get(class_num, f'Class {class_num}'),
                'count': item['count']
            })
        
        return JsonResponse({
            'type': 'pie',
            'data': result_data,
            'label': 'classification_name',
            'value': 'count',
            'title': 'Classification Distribution'
        })
    
    return JsonResponse({'error': 'Invalid chart type'}, status=400)


@login_required
def streamlit_charts(request):
    """Embed Streamlit charts in Django"""
    # This view will embed Streamlit charts using iframe
    streamlit_url = f"http://{settings.STREAMLIT_HOST}:{settings.STREAMLIT_PORT}"
    
    context = {
        'streamlit_url': streamlit_url,
    }
    
    return render(request, 'analytics/streamlit_charts.html', context)
