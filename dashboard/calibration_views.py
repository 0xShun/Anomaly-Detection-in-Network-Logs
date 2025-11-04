"""
Admin Calibration Views for LogBERT Web Platform
Integrates with FastAPI admin API for model recalibration
"""

import json
import requests
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from .models import PlatformSettings
from .forms import CalibrationForm


@staff_member_required
def calibration_dashboard(request):
    """Main calibration interface for admins"""
    # Get current thresholds from FastAPI
    try:
        admin_api_url = getattr(settings, 'ADMIN_API_URL', 'http://localhost:8081')
        response = requests.get(f"{admin_api_url}/thresholds", timeout=5)
        current_thresholds = response.json() if response.status_code == 200 else {}
    except Exception as e:
        current_thresholds = {}
        messages.error(request, f"Could not fetch current thresholds: {e}")
    
    # Get platform settings
    platform_settings = PlatformSettings.objects.first()
    if not platform_settings:
        platform_settings = PlatformSettings.objects.create()
    
    context = {
        'current_thresholds': current_thresholds,
        'platform_settings': platform_settings,
        'available_domains': ['hdfs', 'auth', 'network', 'system'],
        'available_objectives': [
            ('f1', 'F1 Score (Balanced)'),
            ('target_fp', 'Target False Positive Rate')
        ]
    }
    return render(request, 'dashboard/admin/calibration_dashboard.html', context)


@staff_member_required
@require_http_methods(["POST"])
def run_calibration(request):
    """Execute calibration process"""
    try:
        admin_api_url = getattr(settings, 'ADMIN_API_URL', 'http://localhost:8081')
        
        # Extract form data
        calibration_data = {
            'domain': request.POST.get('domain', 'hdfs'),
            'model_version': request.POST.get('model_version', 'current'),
            'objective': request.POST.get('objective', 'f1'),
            'target_fp': float(request.POST.get('target_fp', 0.01)),
        }
        
        # Use existing CSV files or generate from time window
        if request.POST.get('use_existing_csvs'):
            calibration_data.update({
                'normal_csv': request.POST.get('normal_csv'),
                'abnormal_csv': request.POST.get('abnormal_csv'),
            })
        else:
            calibration_data.update({
                'start': request.POST.get('start_time'),
                'end': request.POST.get('end_time'),
            })
        
        # Call FastAPI calibration endpoint
        response = requests.post(
            f"{admin_api_url}/calibrate",
            json=calibration_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            messages.success(
                request, 
                f"Calibration successful! New threshold: {result['result']['threshold']:.4f}"
            )
            
            # Update platform settings with new threshold
            platform_settings = PlatformSettings.objects.first()
            if platform_settings:
                platform_settings.anomaly_threshold = result['result']['threshold']
                platform_settings.save()
                
        else:
            messages.error(request, f"Calibration failed: {response.text}")
            
    except Exception as e:
        messages.error(request, f"Error during calibration: {e}")
    
    return redirect('dashboard:calibration_dashboard')


@staff_member_required
def get_calibration_curves(request):
    """Get performance curves for visualization"""
    try:
        admin_api_url = getattr(settings, 'ADMIN_API_URL', 'http://localhost:8081')
        
        params = {
            'domain': request.GET.get('domain', 'hdfs'),
            'normal_csv': request.GET.get('normal_csv'),
            'abnormal_csv': request.GET.get('abnormal_csv'),
            'steps': int(request.GET.get('steps', 101))
        }
        
        response = requests.get(f"{admin_api_url}/curves", params=params, timeout=10)
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({'error': 'Failed to fetch curves'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
@require_http_methods(["POST"])
def apply_threshold(request):
    """Apply a specific threshold value"""
    try:
        admin_api_url = getattr(settings, 'ADMIN_API_URL', 'http://localhost:8081')
        
        params = {
            'domain': request.POST.get('domain'),
            'model_version': request.POST.get('model_version'),
            'threshold': float(request.POST.get('threshold'))
        }
        
        response = requests.post(f"{admin_api_url}/thresholds/apply", params=params, timeout=5)
        
        if response.status_code == 200:
            messages.success(request, "Threshold applied successfully!")
            
            # Update platform settings
            platform_settings = PlatformSettings.objects.first()
            if platform_settings:
                platform_settings.anomaly_threshold = params['threshold']
                platform_settings.save()
        else:
            messages.error(request, "Failed to apply threshold")
            
    except Exception as e:
        messages.error(request, f"Error applying threshold: {e}")
    
    return redirect('dashboard:calibration_dashboard')


@staff_member_required
@require_http_methods(["POST"])
def reload_thresholds(request):
    """Trigger threshold reload for live services"""
    try:
        admin_api_url = getattr(settings, 'ADMIN_API_URL', 'http://localhost:8081')
        
        response = requests.post(f"{admin_api_url}/thresholds/reload", timeout=5)
        
        if response.status_code == 200:
            messages.success(request, "Threshold reload triggered successfully!")
        else:
            messages.error(request, "Failed to trigger threshold reload")
            
    except Exception as e:
        messages.error(request, f"Error triggering reload: {e}")
    
    return redirect('dashboard:calibration_dashboard')


@staff_member_required
def threshold_history(request):
    """View threshold change history"""
    # This could be enhanced with a ThresholdHistory model
    # to track all threshold changes over time
    context = {
        'title': 'Threshold History',
        'message': 'Threshold history tracking coming soon...'
    }
    return render(request, 'dashboard/admin/threshold_history.html', context)
