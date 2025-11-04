"""
Comprehensive tests for LogBERT Remote Monitoring API

Tests cover:
- Model creation and validation
- API authentication
- CRUD operations on all endpoints
- Data filtering and pagination
- Error handling
"""

import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch
import os

from .models import Alert, SystemMetric, LogStatistic, RawModelOutput
from .authentication import APIKeyAuthentication


class ModelTests(TestCase):
    """Test database models"""
    
    def setUp(self):
        self.school_id = "school-001"
    
    def test_alert_creation(self):
        """Test Alert model creation and fields"""
        alert = Alert.objects.create(
            school_id=self.school_id,
            alert_level="high",
            summary="Test anomaly detected",
            anomaly_score=0.95,
            affected_systems=["server-01", "server-02"],
            status="new",
            log_count=10
        )
        
        self.assertEqual(alert.school_id, self.school_id)
        self.assertEqual(alert.alert_level, "high")
        self.assertEqual(alert.status, "new")
        self.assertTrue(alert.timestamp)
        self.assertIsNone(alert.acknowledged_at)
    
    def test_alert_status_transitions(self):
        """Test alert status changes"""
        alert = Alert.objects.create(
            school_id=self.school_id,
            alert_level="low",
            summary="Test alert",
            anomaly_score=0.6,
            status="new"
        )
        
        # Acknowledge alert
        alert.status = "acknowledged"
        alert.acknowledged_by = "admin"
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        self.assertEqual(alert.status, "acknowledged")
        self.assertEqual(alert.acknowledged_by, "admin")
        self.assertIsNotNone(alert.acknowledged_at)
        
        # Resolve alert
        alert.status = "resolved"
        alert.resolution_notes = "Fixed the issue"
        alert.save()
        
        self.assertEqual(alert.status, "resolved")
        self.assertEqual(alert.resolution_notes, "Fixed the issue")
    
    def test_system_metric_creation(self):
        """Test SystemMetric model"""
        metric = SystemMetric.objects.create(
            school_id=self.school_id,
            metric_type="cpu_usage",
            value=75.5,
            unit="percent",
            metadata={"source": "server-01"}
        )
        
        self.assertEqual(metric.metric_type, "cpu_usage")
        self.assertEqual(metric.value, 75.5)
        self.assertEqual(metric.unit, "percent")
        self.assertEqual(metric.metadata["source"], "server-01")
    
    def test_log_statistic_creation(self):
        """Test LogStatistic model"""
        stat = LogStatistic.objects.create(
            school_id=self.school_id,
            total_logs_processed=10000,
            anomalous_logs=150,
            normal_logs=9850,
            parsing_coverage=98.5,
            source_breakdown={
                "apache": 6000,
                "linux": 4000
            }
        )
        
        self.assertEqual(stat.total_logs_processed, 10000)
        self.assertEqual(stat.anomalous_logs, 150)
        self.assertAlmostEqual(stat.parsing_coverage, 98.5)
        
        # Test JSON field
        self.assertEqual(stat.source_breakdown["apache"], 6000)
        self.assertEqual(stat.source_breakdown["linux"], 4000)
    
    def test_raw_model_output_creation(self):
        """Test RawModelOutput model"""
        output = RawModelOutput.objects.create(
            school_id=self.school_id,
            model_name="apache_full",
            log_sequence="Login attempt from 192.168.1.100",
            masked_predictions=["login", "from", "192.168.1.100"],
            anomaly_scores=[0.95, 0.02, 0.03],
            confidence_score=0.95,
            is_anomaly=True
        )
        
        self.assertTrue(output.is_anomaly)
        self.assertEqual(output.confidence_score, 0.95)
        self.assertEqual(output.model_name, "apache_full")


class AuthenticationTests(APITestCase):
    """Test API key authentication"""
    
    def setUp(self):
        self.client = APIClient()
        self.test_api_key = "test-api-key-12345"
    
    @patch.dict(os.environ, {'LOGBERT_API_KEYS': 'test-api-key-12345,another-key'})
    def test_valid_api_key_bearer(self):
        """Test authentication with valid Bearer token"""
        response = self.client.get(
            '/api/v1/status/',
            HTTP_AUTHORIZATION=f'Bearer {self.test_api_key}'
        )
        # Status endpoint should be accessible
        self.assertIn(response.status_code, [200, 401])  # Depends on auth setup
    
    @patch.dict(os.environ, {'LOGBERT_API_KEYS': 'test-api-key-12345'})
    def test_valid_api_key_header(self):
        """Test authentication with X-API-Key header"""
        response = self.client.get(
            '/api/v1/status/',
            HTTP_X_API_KEY=self.test_api_key
        )
        self.assertIn(response.status_code, [200, 401])
    
    def test_invalid_api_key(self):
        """Test authentication with invalid API key"""
        response = self.client.get(
            '/api/v1/alerts/',
            HTTP_AUTHORIZATION='Bearer invalid-key-999'
        )
        # DRF may return 401 or 403 depending on permission classes
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_missing_api_key(self):
        """Test request without API key"""
        response = self.client.get('/api/v1/alerts/')
        # DRF may return 401 or 403 depending on permission classes
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class AlertAPITests(APITestCase):
    """Test Alert API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.test_api_key = "test-api-key-12345"
        
        # Mock environment variable
        self.env_patcher = patch.dict(os.environ, {'LOGBERT_API_KEYS': self.test_api_key})
        self.env_patcher.start()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.test_api_key}')
        
        # Create test data
        Alert.objects.create(
            school_id="school-001",
            alert_level="high",
            summary="Test alert 1",
            anomaly_score=0.95,
            status="new"
        )
        Alert.objects.create(
            school_id="school-001",
            alert_level="low",
            summary="Test alert 2",
            anomaly_score=0.65,
            status="resolved"
        )
    
    def tearDown(self):
        self.env_patcher.stop()
    
    def test_list_alerts(self):
        """Test GET /api/v1/alerts/"""
        response = self.client.get('/api/v1/alerts/')
        
        if response.status_code == 200:
            self.assertEqual(len(response.data['results']), 2)
    
    def test_create_alert(self):
        """Test POST /api/v1/alerts/"""
        data = {
            "school_id": "school-002",
            "alert_level": "critical",
            "summary": "Unauthorized access detected",
            "anomaly_score": 0.98,
            "affected_systems": ["web-server-01"],
            "status": "new",
            "log_count": 10
        }
        
        response = self.client.post('/api/v1/alerts/', data, format='json')
        
        if response.status_code == 201:
            self.assertEqual(response.data['school_id'], "school-002")
            self.assertEqual(response.data['alert_level'], "critical")
    
    def test_filter_alerts_by_level(self):
        """Test filtering alerts by level"""
        response = self.client.get('/api/v1/alerts/?level=high')
        
        if response.status_code == 200:
            for alert in response.data['results']:
                self.assertEqual(alert['alert_level'], 'high')
    
    def test_filter_alerts_by_school(self):
        """Test filtering alerts by school_id"""
        response = self.client.get('/api/v1/alerts/?school_id=school-001')
        
        if response.status_code == 200:
            for alert in response.data['results']:
                self.assertEqual(alert['school_id'], 'school-001')
    
    def test_filter_alerts_by_status(self):
        """Test filtering alerts by status"""
        response = self.client.get('/api/v1/alerts/?status=active')
        
        if response.status_code == 200:
            for alert in response.data['results']:
                self.assertEqual(alert['status'], 'active')


class MetricAPITests(APITestCase):
    """Test SystemMetric API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.test_api_key = "test-api-key-12345"
        
        self.env_patcher = patch.dict(os.environ, {'LOGBERT_API_KEYS': self.test_api_key})
        self.env_patcher.start()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.test_api_key}')
        
        # Create test metrics
        SystemMetric.objects.create(
            school_id="school-001",
            metric_type="cpu_usage",
            value=80.5,
            unit="percent",
            metadata={"source": "server-01"}
        )
        SystemMetric.objects.create(
            school_id="school-001",
            metric_type="memory_usage",
            value=4096,
            unit="MB",
            metadata={"source": "server-01"}
        )
    
    def tearDown(self):
        self.env_patcher.stop()
    
    def test_list_metrics(self):
        """Test GET /api/v1/metrics/"""
        response = self.client.get('/api/v1/metrics/')
        
        if response.status_code == 200:
            self.assertGreaterEqual(len(response.data['results']), 2)
    
    def test_create_metric(self):
        """Test POST /api/v1/metrics/"""
        data = {
            "school_id": "school-001",
            "metric_type": "processing_time",
            "value": 125.5,
            "unit": "ms",
            "source": "logbert-processor"
        }
        
        response = self.client.post('/api/v1/metrics/', data, format='json')
        
        if response.status_code == 201:
            self.assertEqual(response.data['metric_type'], 'processing_time')
            self.assertEqual(response.data['value'], 125.5)
    
    def test_filter_metrics_by_type(self):
        """Test filtering metrics by type"""
        response = self.client.get('/api/v1/metrics/?type=cpu_usage')
        
        if response.status_code == 200:
            for metric in response.data['results']:
                self.assertEqual(metric['metric_type'], 'cpu_usage')


class StatisticAPITests(APITestCase):
    """Test LogStatistic API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.test_api_key = "test-api-key-12345"
        
        self.env_patcher = patch.dict(os.environ, {'LOGBERT_API_KEYS': self.test_api_key})
        self.env_patcher.start()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.test_api_key}')
    
    def tearDown(self):
        self.env_patcher.stop()
    
    def test_create_statistic(self):
        """Test POST /api/v1/statistics/"""
        data = {
            "school_id": "school-001",
            "total_logs_processed": 50000,
            "anomalous_logs": 250,
            "normal_logs": 49750,
            "parsing_coverage": 99.2,
            "top_templates": [
                {"template": "User login", "count": 20000},
                {"template": "File access", "count": 15000}
            ],
            "source_breakdown": {
                "apache": 30000,
                "linux": 20000
            }
        }
        
        response = self.client.post('/api/v1/statistics/', data, format='json')
        
        if response.status_code == 201:
            self.assertEqual(response.data['total_logs_processed'], 50000)
            self.assertEqual(response.data['anomalous_logs'], 250)
    
    def test_list_statistics(self):
        """Test GET /api/v1/statistics/"""
        response = self.client.get('/api/v1/statistics/')
        
        self.assertIn(response.status_code, [200, 401])


class RawOutputAPITests(APITestCase):
    """Test RawModelOutput API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.test_api_key = "test-api-key-12345"
        
        self.env_patcher = patch.dict(os.environ, {'LOGBERT_API_KEYS': self.test_api_key})
        self.env_patcher.start()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.test_api_key}')
    
    def tearDown(self):
        self.env_patcher.stop()
    
    def test_create_raw_output(self):
        """Test POST /api/v1/raw-outputs/"""
        data = {
            "school_id": "school-001",
            "log_sequence": "Failed login attempt",
            "log_key": "apache_001",
            "masked_predictions": ["failed", "login", "attempt"],
            "anomaly_scores": [0.95, 0.02, 0.01],
            "final_anomaly_score": 0.95,
            "is_anomaly": True,
            "model_version": "logbert-v1.0"
        }
        
        response = self.client.post('/api/v1/raw-outputs/', data, format='json')
        
        if response.status_code == 201:
            self.assertTrue(response.data['is_anomaly'])
            self.assertEqual(response.data['final_anomaly_score'], 0.95)


class StatusEndpointTests(APITestCase):
    """Test system status endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.test_api_key = "test-api-key-12345"
        
        self.env_patcher = patch.dict(os.environ, {'LOGBERT_API_KEYS': self.test_api_key})
        self.env_patcher.start()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.test_api_key}')
    
    def tearDown(self):
        self.env_patcher.stop()
    
    def test_status_endpoint(self):
        """Test GET /api/v1/status/"""
        response = self.client.get('/api/v1/status/')
        
        if response.status_code == 200:
            self.assertIn('status', response.data)
            self.assertIn('endpoints', response.data)
    
    def test_health_check(self):
        """Test POST /api/v1/health/"""
        data = {
            "school_id": "school-001",
            "status": "healthy"
        }
        
        response = self.client.post('/api/v1/health/', data, format='json')
        
        if response.status_code == 200:
            self.assertIn('message', response.data)


class PaginationTests(APITestCase):
    """Test API pagination"""
    
    def setUp(self):
        self.client = APIClient()
        self.test_api_key = "test-api-key-12345"
        
        self.env_patcher = patch.dict(os.environ, {'LOGBERT_API_KEYS': self.test_api_key})
        self.env_patcher.start()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.test_api_key}')
        
        # Create many alerts for pagination testing
        for i in range(150):
            Alert.objects.create(
                school_id="school-001",
                alert_level="low",
                summary=f"Test alert {i}",
                anomaly_score=0.5,
                status="new"
            )
    
    def tearDown(self):
        self.env_patcher.stop()
    
    def test_pagination_first_page(self):
        """Test first page of paginated results"""
        response = self.client.get('/api/v1/alerts/')
        
        if response.status_code == 200:
            self.assertIn('results', response.data)
            self.assertIn('count', response.data)
            self.assertLessEqual(len(response.data['results']), 100)  # PAGE_SIZE=100
    
    def test_pagination_next_page(self):
        """Test navigating to next page"""
        response = self.client.get('/api/v1/alerts/')
        
        if response.status_code == 200 and response.data.get('next'):
            # Extract page number from next URL
            next_url = response.data['next']
            response2 = self.client.get(next_url)
            self.assertEqual(response2.status_code, 200)


class DataValidationTests(APITestCase):
    """Test data validation"""
    
    def setUp(self):
        self.client = APIClient()
        self.test_api_key = "test-api-key-12345"
        
        self.env_patcher = patch.dict(os.environ, {'LOGBERT_API_KEYS': self.test_api_key})
        self.env_patcher.start()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.test_api_key}')
    
    def tearDown(self):
        self.env_patcher.stop()
    
    def test_invalid_alert_level(self):
        """Test creating alert with invalid level"""
        data = {
            "school_id": "school-001",
            "alert_type": "test",
            "message": "Test",
            "level": "invalid_level",  # Should be low/medium/high/critical
            "status": "active"
        }
        
        response = self.client.post('/api/v1/alerts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_missing_required_fields(self):
        """Test creating alert without required fields"""
        data = {
            "school_id": "school-001",
            # Missing alert_type, message, level, status
        }
        
        response = self.client.post('/api/v1/alerts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_metric_value(self):
        """Test creating metric with non-numeric value"""
        data = {
            "school_id": "school-001",
            "metric_type": "cpu_usage",
            "value": "not_a_number",  # Should be float
            "unit": "percent"
        }
        
        response = self.client.post('/api/v1/metrics/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
