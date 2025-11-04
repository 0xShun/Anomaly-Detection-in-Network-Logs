from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import LogEntry, Anomaly
from .utils import invalidate_log_caches


@receiver(post_save, sender=LogEntry)
def invalidate_caches_on_log_save(sender, **kwargs):
    """Invalidate relevant caches when a new log entry is saved"""
    invalidate_log_caches()


@receiver(post_delete, sender=LogEntry)
def invalidate_caches_on_log_delete(sender, **kwargs):
    """Invalidate relevant caches when a log entry is deleted"""
    invalidate_log_caches()


@receiver(post_save, sender=Anomaly)
def invalidate_caches_on_anomaly_save(sender, **kwargs):
    """Invalidate relevant caches when a new anomaly is saved"""
    # Clear anomaly-specific caches
    cache_keys = [
        'recent_anomalies_10',
        'recent_anomalies_5',
        'system_metrics',
    ]
    cache.delete_many(cache_keys)


@receiver(post_delete, sender=Anomaly)
def invalidate_caches_on_anomaly_delete(sender, **kwargs):
    """Invalidate relevant caches when an anomaly is deleted"""
    # Clear anomaly-specific caches
    cache_keys = [
        'recent_anomalies_10',
        'recent_anomalies_5',
        'system_metrics',
    ]
    cache.delete_many(cache_keys)
