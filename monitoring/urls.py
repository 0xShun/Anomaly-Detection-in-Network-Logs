from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('', views.system_monitoring, name='system_monitoring'),
    path('api/system-status/', views.api_system_status, name='api_system_status'),
    path('api/log-ingestion-rate/', views.api_log_ingestion_rate, name='api_log_ingestion_rate'),
] 