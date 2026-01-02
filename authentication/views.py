from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json


def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('dashboard:overview')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_active:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard:overview')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'authentication/login.html')


@login_required
def logout_view(request):
    """Custom logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('authentication:login')


@login_required
def settings_view(request):
    """Main settings page view"""
    from .models import UserPreferences
    
    # Create preferences if they don't exist
    preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    
    context = {
        'preferences': preferences
    }
    return render(request, 'authentication/settings.html', context)


@login_required
def update_profile(request):
    """Update user profile information"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()
        
        messages.success(request, 'Profile updated successfully.')
    
    return redirect('authentication:settings')


@login_required
def update_preferences(request):
    """Update user preferences"""
    from .models import UserPreferences
    
    if request.method == 'POST':
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        
        # Display Settings
        preferences.dark_mode = request.POST.get('dark_mode') == 'on'
        preferences.compact_view = request.POST.get('compact_view') == 'on'
        
        # Data Settings
        preferences.refresh_interval = int(request.POST.get('refresh_interval', 10))
        preferences.items_per_page = int(request.POST.get('items_per_page', 25))
        preferences.timezone = request.POST.get('timezone', 'UTC')
        
        preferences.save()
        messages.success(request, 'Preferences updated successfully.')
    
    return redirect('authentication:settings')


@login_required
def update_notifications(request):
    """Update notification preferences"""
    from .models import UserPreferences
    
    if request.method == 'POST':
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        
        # Email Notifications
        preferences.email_anomalies = request.POST.get('email_anomalies') == 'on'
        preferences.email_critical = request.POST.get('email_critical') == 'on'
        preferences.email_reports = request.POST.get('email_reports') == 'on'
        preferences.email_updates = request.POST.get('email_updates') == 'on'
        
        # Browser Notifications
        preferences.browser_notifications = request.POST.get('browser_notifications') == 'on'
        
        preferences.save()
        messages.success(request, 'Notification settings updated successfully.')
    
    return redirect('authentication:settings')


@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('authentication:settings')
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('authentication:settings')
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('authentication:settings')
        
        request.user.set_password(new_password)
        request.user.save()
        
        # Re-authenticate user
        user = authenticate(username=request.user.username, password=new_password)
        login(request, user)
        
        messages.success(request, 'Password changed successfully.')
        return redirect('authentication:settings')
    
    return render(request, 'authentication/change_password.html')


@csrf_exempt
def api_login(request):
    """API endpoint for login (for AJAX requests)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None and user.is_active:
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful',
                    'redirect_url': '/dashboard/'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid username or password'
                }, status=401)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)
