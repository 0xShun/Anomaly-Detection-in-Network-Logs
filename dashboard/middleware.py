import time
import logging
from django.core.cache import cache
from django.conf import settings


logger = logging.getLogger(__name__)


class PerformanceMonitoringMiddleware:
    """Middleware to monitor request performance and log slow queries"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD', 2.0)  # 2 seconds
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Add response time header
        response['X-Response-Time'] = f"{duration:.3f}s"
        
        # Log slow requests
        if duration > self.slow_threshold:
            logger.warning(
                f"Slow request detected: {request.method} {request.path} "
                f"took {duration:.3f}s (threshold: {self.slow_threshold}s)"
            )
        
        # Update performance metrics in cache
        self._update_performance_metrics(request.path, duration)
        
        return response
    
    def _update_performance_metrics(self, path, duration):
        """Update performance metrics in cache"""
        try:
            cache_key = f"perf_metrics_{path.replace('/', '_')}"
            metrics = cache.get(cache_key, {'count': 0, 'total_time': 0, 'avg_time': 0})
            
            metrics['count'] += 1
            metrics['total_time'] += duration
            metrics['avg_time'] = metrics['total_time'] / metrics['count']
            
            # Cache for 1 hour
            cache.set(cache_key, metrics, 3600)
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")


class CacheHitRateMiddleware:
    """Middleware to track cache hit rates"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Track cache hits for this request
        cache_hits = getattr(cache, '_hits', 0)
        cache_misses = getattr(cache, '_misses', 0)
        
        response = self.get_response(request)
        
        # Calculate hit rate for this request
        new_hits = getattr(cache, '_hits', 0) - cache_hits
        new_misses = getattr(cache, '_misses', 0) - cache_misses
        
        if new_hits + new_misses > 0:
            hit_rate = new_hits / (new_hits + new_misses) * 100
            response['X-Cache-Hit-Rate'] = f"{hit_rate:.1f}%"
        
        return response


class DatabaseQueryCountMiddleware:
    """Middleware to count database queries per request"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from django.db import connection
        
        # Get initial query count
        initial_queries = len(connection.queries)
        
        response = self.get_response(request)
        
        # Calculate queries for this request
        query_count = len(connection.queries) - initial_queries
        
        # Add query count header
        response['X-DB-Queries'] = str(query_count)
        
        # Log requests with many queries
        if query_count > 10:
            logger.warning(
                f"High query count: {request.method} {request.path} "
                f"made {query_count} database queries"
            )
        
        return response
