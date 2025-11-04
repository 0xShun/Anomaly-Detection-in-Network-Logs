from django.urls import path
from . import views
from . import calibration_views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_overview, name='overview'),
    path('logs/', views.log_details, name='log_details'),
    path('api/dashboard-data/', views.api_dashboard_data, name='api_dashboard_data'),
    path('api/anomaly-feed/', views.api_anomaly_feed, name='api_anomaly_feed'),
    # New API endpoints for Streamlit
    path('api/streamlit/chart-data/', views.api_streamlit_chart_data, name='api_streamlit_chart_data'),
    path('api/streamlit/anomaly-data/', views.api_streamlit_anomaly_data, name='api_streamlit_anomaly_data'),
    path('api/streamlit/system-metrics/', views.api_streamlit_system_metrics, name='api_streamlit_system_metrics'),
    
    # Admin Calibration URLs
    path('admin/calibration/', calibration_views.calibration_dashboard, name='calibration_dashboard'),
    path('admin/calibration/run/', calibration_views.run_calibration, name='run_calibration'),
    path('admin/calibration/curves/', calibration_views.get_calibration_curves, name='get_calibration_curves'),
    path('admin/calibration/apply/', calibration_views.apply_threshold, name='apply_threshold'),
    path('admin/calibration/reload/', calibration_views.reload_thresholds, name='reload_thresholds'),
    path('admin/calibration/history/', calibration_views.threshold_history, name='threshold_history'),
    # Pipeline run endpoints (trigger sample data + performance analysis)
    path('run/pipeline/', views.run_pipeline, name='run_pipeline'),
    path('run/pipeline/status/', views.pipeline_status, name='pipeline_status'),
] 