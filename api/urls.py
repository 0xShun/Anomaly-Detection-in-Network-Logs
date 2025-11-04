"""API URL configuration."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'alerts', views.AlertViewSet, basename='alert')
router.register(r'metrics', views.SystemMetricViewSet, basename='metric')
router.register(r'statistics', views.LogStatisticViewSet, basename='statistic')
router.register(r'raw-outputs', views.RawModelOutputViewSet, basename='raw-output')

urlpatterns = [
    # Status and health endpoints
    path('status/', views.api_status, name='api-status'),
    path('health/', views.health_check, name='api-health'),
    
    # Include router URLs
    path('', include(router.urls)),
]
