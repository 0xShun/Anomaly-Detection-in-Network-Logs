from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('settings/', views.settings_view, name='settings'),
    path('change-password/', views.change_password, name='change_password'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('update-preferences/', views.update_preferences, name='update_preferences'),
    path('update-notifications/', views.update_notifications, name='update_notifications'),
    path('api/login/', views.api_login, name='api_login'),
] 