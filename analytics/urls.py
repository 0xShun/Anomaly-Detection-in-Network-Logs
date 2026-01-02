from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='analytics_dashboard'),
    path('api/chart-data/', views.api_chart_data, name='api_chart_data'),
    path('streamlit/', views.streamlit_charts, name='streamlit_charts'),
] 