#!/usr/bin/env python
"""
API Testing Script for LogBERT Remote Monitoring Platform

This script tests all API endpoints to ensure they're working correctly.

Usage:
    export LOGBERT_API_KEY="your-api-key"
    export LOGBERT_REMOTE_URL="https://yourusername.pythonanywhere.com"
    python test_api.py

Or for local testing:
    export LOGBERT_API_KEY="your-api-key"
    export LOGBERT_REMOTE_URL="http://localhost:8000"
    python test_api.py
"""

import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

def test_api():
    """Test all API endpoints."""
    
    api_key = os.environ.get('LOGBERT_API_KEY')
    base_url = os.environ.get('LOGBERT_REMOTE_URL', 'http://localhost:8000')
    
    if not api_key:
        print("ERROR: LOGBERT_API_KEY not set")
        sys.exit(1)
    
    base_url = base_url.rstrip('/')
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    
    print(f"Testing API at: {base_url}")
    print("=" * 60)
    
    # Test 1: Status endpoint
    print("\n1. Testing /api/v1/status/")
    try:
        response = requests.get(f"{base_url}/api/v1/status/", headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 2: Health check
    print("\n2. Testing /api/v1/health/")
    health_data = {
        'school_id': 'test_school',
        'status': 'running',
        'last_analysis': datetime.now().isoformat(),
        'components': {'parser': 'ok', 'model': 'ok'}
    }
    try:
        response = requests.post(f"{base_url}/api/v1/health/", headers=headers, json=health_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 3: Post alert
    print("\n3. Testing /api/v1/alerts/ (POST)")
    alert_data = {
        'timestamp': datetime.now().isoformat(),
        'school_id': 'test_school',
        'alert_level': 'high',
        'anomaly_score': 0.89,
        'affected_systems': ['test_system'],
        'summary': 'Test alert from API test script',
        'log_count': 100
    }
    try:
        response = requests.post(f"{base_url}/api/v1/alerts/", headers=headers, json=alert_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            print(f"   ✓ Alert created: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 4: Get alerts
    print("\n4. Testing /api/v1/alerts/ (GET)")
    try:
        response = requests.get(f"{base_url}/api/v1/alerts/", headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('results', data) if isinstance(data, dict) else data)
            print(f"   ✓ Retrieved {count} alerts")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 5: Post metric
    print("\n5. Testing /api/v1/metrics/ (POST)")
    metric_data = {
        'timestamp': datetime.now().isoformat(),
        'school_id': 'test_school',
        'metric_type': 'cpu_usage',
        'value': 45.5,
        'unit': 'percent',
        'metadata': {'host': 'test-server'}
    }
    try:
        response = requests.post(f"{base_url}/api/v1/metrics/", headers=headers, json=metric_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            print(f"   ✓ Metric created")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 6: Post statistics
    print("\n6. Testing /api/v1/statistics/ (POST)")
    stats_data = {
        'timestamp': datetime.now().isoformat(),
        'school_id': 'test_school',
        'total_logs_processed': 10000,
        'normal_logs': 9800,
        'anomalous_logs': 200,
        'parsing_coverage': 99.5,
        'templates_extracted': 45,
        'processing_time_seconds': 120.5,
        'logs_per_second': 83.0,
        'source_breakdown': {'apache': 5000, 'linux': 3000, 'ssh': 2000}
    }
    try:
        response = requests.post(f"{base_url}/api/v1/statistics/", headers=headers, json=stats_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            print(f"   ✓ Statistics created")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 7: Post raw output
    print("\n7. Testing /api/v1/raw-outputs/ (POST)")
    raw_output_data = {
        'timestamp': datetime.now().isoformat(),
        'school_id': 'test_school',
        'model_name': 'apache_full',
        'log_sequence': 'Test log sequence data',
        'masked_predictions': {'token_0': 'prediction_0'},
        'anomaly_scores': [0.1, 0.2, 0.9],
        'is_anomaly': True,
        'confidence_score': 0.89,
        'metadata': {'test': True}
    }
    try:
        response = requests.post(f"{base_url}/api/v1/raw-outputs/", headers=headers, json=raw_output_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            print(f"   ✓ Raw output created")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    print("\n" + "=" * 60)
    print("API testing complete!")

if __name__ == '__main__':
    test_api()
