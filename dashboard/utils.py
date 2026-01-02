from django.core.cache import cache
from django.db.models import Count, Case, When, IntegerField, Q
from django.utils import timezone
from datetime import timedelta
from .models import LogEntry, Anomaly, SystemStatus
from django.conf import settings


def get_cached_log_stats():
    """Get log statistics with caching"""
    cache_key = 'log_stats'
    stats = cache.get(cache_key)
    
    if stats is None:
        # Single aggregation query instead of multiple counts
        stats = LogEntry.objects.aggregate(
            total_logs=Count('id'),
            error_count=Count(Case(
                When(log_type__iexact='ERROR', then=1),
                output_field=IntegerField()
            )),
            warning_count=Count(Case(
                When(log_type__iexact='WARNING', then=1),
                output_field=IntegerField()
            )),
            info_count=Count(Case(
                When(log_type__iexact='INFO', then=1),
                output_field=IntegerField()
            )),
            debug_count=Count(Case(
                When(log_type__iexact='DEBUG', then=1),
                output_field=IntegerField()
            ))
        )
        
        # Cache for 5 minutes
        cache.set(cache_key, stats, getattr(settings, 'CACHE_TTL', {}).get('log_counts', 300))
    
    return stats


def get_cached_recent_anomalies(limit=10):
    """Get recent anomalies with caching and optimized query"""
    cache_key = f'recent_anomalies_{limit}'
    anomalies = cache.get(cache_key)
    
    if anomalies is None:
        # Optimized query with select_related
        anomalies_qs = Anomaly.objects.select_related('log_entry')\
                                     .order_by('-detected_at')[:limit]
        
        # Convert to list to cache
        anomalies = [{
            'id': anomaly.id,
            'log_entry_id': anomaly.log_entry.id,
            'timestamp': anomaly.log_entry.timestamp,
            'host_ip': anomaly.log_entry.host_ip,
            'log_message': anomaly.log_entry.log_message[:100] + '...' if len(anomaly.log_entry.log_message) > 100 else anomaly.log_entry.log_message,
            'anomaly_score': anomaly.anomaly_score,
            'detected_at': anomaly.detected_at,
            'classification_class': anomaly.classification_class,
            'classification_name': anomaly.classification_name or 'Unknown',
            'severity': anomaly.severity or 'info',
            'is_anomaly': anomaly.is_anomaly,
        } for anomaly in anomalies_qs]
        
        # Cache for 1 minute
        cache.set(cache_key, anomalies, 60)
    
    return anomalies


def get_cached_hourly_chart_data(hours=24):
    """Get hourly chart data with database aggregation and caching"""
    cache_key = f'hourly_chart_data_{hours}'
    data = cache.get(cache_key)
    
    if data is None:
        from django.db.models.functions import TruncHour
        
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Use database aggregation instead of Python loops
        hourly_data = LogEntry.objects.filter(
            timestamp__range=(start_time, end_time)
        ).annotate(
            hour=TruncHour('timestamp')
        ).values('hour').annotate(
            total_logs=Count('id'),
            error_logs=Count(Case(When(log_type='error', then=1))),
            warning_logs=Count(Case(When(log_type='warning', then=1))),
            info_logs=Count(Case(When(log_type='info', then=1))),
            debug_logs=Count(Case(When(log_type='debug', then=1)))
        ).order_by('hour')
        
        # Convert to list for caching
        data = list(hourly_data)
        
        # Cache for 10 minutes
        cache.set(cache_key, data, getattr(settings, 'CACHE_TTL', {}).get('chart_data', 600))
    
    return data


def get_optimized_filtered_logs(host_ip=None, log_type=None, date_from=None, date_to=None):
    """Get filtered logs with optimized query"""
    # Start with base queryset
    logs = LogEntry.objects.all()
    
    # Build filters efficiently
    filters = Q()
    
    if host_ip:
        filters &= Q(host_ip__icontains=host_ip)
    
    if log_type:
        filters &= Q(log_type=log_type)
    
    if date_from:
        try:
            from datetime import datetime
            from_datetime = datetime.fromisoformat(date_from.replace('T', ' '))
            filters &= Q(timestamp__gte=from_datetime)
        except ValueError:
            pass
    
    if date_to:
        try:
            from datetime import datetime
            to_datetime = datetime.fromisoformat(date_to.replace('T', ' '))
            filters &= Q(timestamp__lte=to_datetime)
        except ValueError:
            pass
    
    # Apply filters and order
    if filters:
        logs = logs.filter(filters)
    
    return logs.order_by('-timestamp')


def get_cached_log_distributions(hours=24):
    """Get log type and source distributions with caching"""
    cache_key = f'log_distributions_{hours}'
    data = cache.get(cache_key)
    
    if data is None:
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        logs = LogEntry.objects.filter(timestamp__range=(start_time, end_time))
        
        # Get distributions in single queries
        log_type_distribution = list(
            logs.values('log_type')
                .annotate(count=Count('log_type'))
                .order_by('-count')
        )
        
        host_distribution = list(
            logs.values('host_ip')
                .annotate(count=Count('host_ip'))
                .order_by('-count')[:10]
        )
        
        source_distribution = list(
            logs.values('source')
                .annotate(count=Count('source'))
                .order_by('-count')
        )
        
        data = {
            'log_type_distribution': log_type_distribution,
            'host_distribution': host_distribution,
            'source_distribution': source_distribution,
        }
        
        # Cache for 10 minutes
        cache.set(cache_key, data, getattr(settings, 'CACHE_TTL', {}).get('chart_data', 600))
    
    return data


def invalidate_log_caches():
    """Invalidate all log-related caches when new data is added"""
    cache_keys = [
        'log_stats',
        'recent_anomalies_10',
        'recent_anomalies_5',
    ]
    
    # Clear specific cache keys
    cache.delete_many(cache_keys)
    
    # Clear pattern-based caches
    for hours in [1, 6, 12, 24, 48]:
        cache.delete(f'hourly_chart_data_{hours}')
        cache.delete(f'log_distributions_{hours}')


def get_cached_system_metrics():
    """Get system metrics with caching"""
    cache_key = 'system_metrics'
    metrics = cache.get(cache_key)
    
    if metrics is None:
        # Get recent activity (last 24 hours)
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=24)
        
        recent_logs = LogEntry.objects.filter(timestamp__range=(start_time, end_time))
        recent_anomalies = Anomaly.objects.filter(
            log_entry__timestamp__range=(start_time, end_time)
        )
        
        # Calculate metrics
        logs_count = recent_logs.count()
        anomalies_count = recent_anomalies.count()
        logs_per_hour = logs_count / 24
        anomalies_per_hour = anomalies_count / 24
        anomaly_rate = (anomalies_count / logs_count * 100) if logs_count > 0 else 0
        
        # Get top sources and hosts
        top_sources = list(
            recent_logs.values('source')
                      .annotate(count=Count('id'))
                      .order_by('-count')[:5]
        )
        
        top_hosts = list(
            recent_logs.values('host_ip')
                      .annotate(count=Count('id'))
                      .order_by('-count')[:5]
        )
        
        metrics = {
            'logs_per_hour': round(logs_per_hour, 2),
            'anomalies_per_hour': round(anomalies_per_hour, 2),
            'anomaly_rate_percent': round(anomaly_rate, 2),
            'total_logs_24h': logs_count,
            'total_anomalies_24h': anomalies_count,
            'top_sources': top_sources,
            'top_hosts': top_hosts,
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, metrics, getattr(settings, 'CACHE_TTL', {}).get('system_status', 300))
    
    return metrics


def get_cached_classification_stats():
    """Get classification statistics from Anomaly model"""
    cache_key = 'classification_stats'
    stats = cache.get(cache_key)
    
    if stats is None:
        # Class names mapping
        class_names = {
            0: 'Normal',
            1: 'Security Anomaly',
            2: 'System Failure',
            3: 'Performance Issue',
            4: 'Network Anomaly',
            5: 'Config Error',
            6: 'Hardware Issue'
        }
        
        # Get counts for each classification class
        stats = {}
        for class_num in range(7):
            count = Anomaly.objects.filter(classification_class=class_num).count()
            stats[class_num] = {
                'count': count,
                'name': class_names.get(class_num, f'Class {class_num}')
            }
        
        # Cache for 2 minutes (frequent updates during demo)
        cache.set(cache_key, stats, 120)
    
    return stats

