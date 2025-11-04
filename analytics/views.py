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
    
    # Calculate average response time (mock data for now)
    avg_response_time = 245  # milliseconds
    
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
    
    context = {
        'total_logs': total_logs,
        'total_anomalies': total_anomalies,
        'anomaly_rate': anomaly_rate,
        'avg_response_time': avg_response_time,
        'anomalies_by_date': list(anomalies_by_date),
        'anomalies_by_source': list(anomalies_by_source),
        'anomaly_categories': list(anomaly_categories),
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def api_chart_data(request):
    """API endpoint for chart data"""
    chart_type = request.GET.get('type', 'line')
    days = int(request.GET.get('days', 7))
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    if chart_type == 'line':
        # Anomalies over time
        data = Anomaly.objects.filter(
            detected_at__range=(start_date, end_date)
        ).extra(
            select={'date': 'date(detected_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        return JsonResponse({
            'type': 'line',
            'data': list(data),
            'x_axis': 'date',
            'y_axis': 'count',
            'title': f'Anomalies Over Time (Last {days} days)'
        })
    
    elif chart_type == 'bar':
        # Anomalies by source
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
            'title': f'Anomalies by Source (Last {days} days)'
        })
    
    elif chart_type == 'pie':
        # Anomaly categories
        data = Anomaly.objects.filter(
            detected_at__range=(start_date, end_date)
        ).values('log_entry__log_type').annotate(
            count=Count('id')
        ).exclude(log_entry__log_type='').order_by('-count')[:10]
        
        return JsonResponse({
            'type': 'pie',
            'data': list(data),
            'label': 'log_entry__log_type',
            'value': 'count',
            'title': f'Anomaly Categories (Last {days} days)'
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
