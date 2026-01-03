from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from dashboard.models import LogEntry, Anomaly
import json

# Get the custom user model
User = get_user_model()


class AnalyticsChartDataTestCase(TestCase):
    """Test suite for analytics chart data API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test log entries with different classifications
        self.base_time = timezone.now()
        
        # Create logs at different minutes with various classifications
        self.test_logs = []
        
        # Minute 1: Mixed classifications
        for i in range(5):
            log = LogEntry.objects.create(
                log_message=f"Test log {i}",
                timestamp=self.base_time,
                log_type='INFO',
                source='test_source',
                classification_class=0,  # Normal
                classification_name='Normal',
                severity='info',
                anomaly_score=0.1
            )
            self.test_logs.append(log)
        
        # Security anomaly
        log = LogEntry.objects.create(
            log_message="Security test",
            timestamp=self.base_time,
            log_type='ERROR',
            source='test_source',
            classification_class=1,  # Security
            classification_name='Security Anomaly',
            severity='critical',
            anomaly_score=0.95
        )
        self.test_logs.append(log)
        
        # System Failure
        log = LogEntry.objects.create(
            log_message="System failure test",
            timestamp=self.base_time,
            log_type='ERROR',
            source='test_source',
            classification_class=2,  # System Failure
            classification_name='System Failure',
            severity='high',
            anomaly_score=0.88
        )
        self.test_logs.append(log)
        
        # Minute 2: Different classifications
        minute_2 = self.base_time + timedelta(minutes=1)
        
        for i in range(3):
            LogEntry.objects.create(
                log_message=f"Performance test {i}",
                timestamp=minute_2,
                log_type='WARNING',
                source='test_source',
                classification_class=3,  # Performance
                classification_name='Performance Issue',
                severity='medium',
                anomaly_score=0.65
            )
        
        for i in range(2):
            LogEntry.objects.create(
                log_message=f"Network test {i}",
                timestamp=minute_2,
                log_type='ERROR',
                source='test_source',
                classification_class=4,  # Network
                classification_name='Network Anomaly',
                severity='high',
                anomaly_score=0.78
            )
        
        # Minute 3: More classifications
        minute_3 = self.base_time + timedelta(minutes=2)
        
        LogEntry.objects.create(
            log_message="Config test",
            timestamp=minute_3,
            log_type='WARNING',
            source='test_source',
            classification_class=5,  # Config
            classification_name='Config Error',
            severity='medium',
            anomaly_score=0.72
        )
        
        LogEntry.objects.create(
            log_message="Hardware test",
            timestamp=minute_3,
            log_type='ERROR',
            source='test_source',
            classification_class=6,  # Hardware
            classification_name='Hardware Issue',
            severity='high',
            anomaly_score=0.81
        )
    
    def test_line_chart_data_structure(self):
        """Test that line chart (volume over time) returns correct data structure"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'line'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify response structure
        self.assertIn('type', data)
        self.assertIn('data', data)
        self.assertIn('title', data)
        self.assertEqual(data['type'], 'line')
        self.assertEqual(data['title'], 'Log Volume Over Time (By Minute)')
        
        # Verify data is a list
        self.assertIsInstance(data['data'], list)
        
        # Verify each data point has required fields
        if len(data['data']) > 0:
            first_point = data['data'][0]
            self.assertIn('minute', first_point)
            
            # Check all classification classes (0-6) are present
            for i in range(7):
                self.assertIn(f'class_{i}', first_point)
    
    def test_line_chart_data_accuracy(self):
        """Test that line chart returns accurate counts for each classification"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'line'})
        data = json.loads(response.content)
        
        # Count total logs across all time periods and classifications
        total_logs = 0
        for time_point in data['data']:
            for i in range(7):
                total_logs += time_point[f'class_{i}']
        
        # Should match total log entries created
        expected_total = LogEntry.objects.count()
        self.assertEqual(total_logs, expected_total)
        
        # Verify specific minute has correct counts
        # First minute should have 5 Normal, 1 Security, 1 System Failure
        first_minute_data = data['data'][0]
        self.assertEqual(first_minute_data['class_0'], 5)  # Normal
        self.assertEqual(first_minute_data['class_1'], 1)  # Security
        self.assertEqual(first_minute_data['class_2'], 1)  # System Failure
    
    def test_line_chart_stacked_format(self):
        """Test that line chart data is properly formatted for stacked visualization"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'line'})
        data = json.loads(response.content)
        
        # Verify all time points have all 7 classification fields
        for time_point in data['data']:
            for i in range(7):
                class_key = f'class_{i}'
                self.assertIn(class_key, time_point)
                # Values should be integers >= 0
                self.assertIsInstance(time_point[class_key], int)
                self.assertGreaterEqual(time_point[class_key], 0)
    
    def test_pie_chart_data_structure(self):
        """Test that pie chart (classification distribution) returns correct structure"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'pie'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify response structure
        self.assertIn('type', data)
        self.assertIn('data', data)
        self.assertIn('title', data)
        self.assertEqual(data['type'], 'pie')
        self.assertEqual(data['title'], 'Classification Distribution')
        
        # Verify data is a list
        self.assertIsInstance(data['data'], list)
        
        # Verify each data point has required fields
        for item in data['data']:
            self.assertIn('classification_class', item)
            self.assertIn('classification_name', item)
            self.assertIn('count', item)
    
    def test_pie_chart_data_accuracy(self):
        """Test that pie chart returns accurate classification counts"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'pie'})
        data = json.loads(response.content)
        
        # Sum all counts
        total_count = sum(item['count'] for item in data['data'])
        
        # Should match total log entries
        expected_total = LogEntry.objects.count()
        self.assertEqual(total_count, expected_total)
        
        # Verify specific classification counts
        classification_counts = {item['classification_class']: item['count'] for item in data['data']}
        
        # We created: 5 Normal (0), 1 Security (1), 1 System Failure (2),
        # 3 Performance (3), 2 Network (4), 1 Config (5), 1 Hardware (6)
        expected_counts = {0: 5, 1: 1, 2: 1, 3: 3, 4: 2, 5: 1, 6: 1}
        
        for class_num, expected_count in expected_counts.items():
            if class_num in classification_counts:
                self.assertEqual(classification_counts[class_num], expected_count,
                               f"Classification {class_num} count mismatch")
    
    def test_pie_chart_classification_names(self):
        """Test that pie chart returns correct classification names"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'pie'})
        data = json.loads(response.content)
        
        # Create mapping of classification_class to name
        class_to_name = {item['classification_class']: item['classification_name'] 
                         for item in data['data']}
        
        # Verify expected names
        expected_names = {
            0: 'Normal',
            1: 'Security Anomaly',
            2: 'System Failure',
            3: 'Performance Issue',
            4: 'Network Anomaly',
            5: 'Config Error',
            6: 'Hardware Issue'
        }
        
        for class_num, name in class_to_name.items():
            if class_num in expected_names:
                self.assertEqual(name, expected_names[class_num],
                               f"Classification {class_num} name mismatch")
    
    def test_invalid_chart_type(self):
        """Test that invalid chart type returns error"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'invalid'})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access chart data"""
        # Don't login
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'line'})
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_no_data_scenario(self):
        """Test chart data with no log entries"""
        # Delete all log entries
        LogEntry.objects.all().delete()
        
        self.client.login(username='testuser', password='testpass123')
        
        # Line chart
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'line'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['data']), 0)
        
        # Pie chart
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'pie'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['data']), 0)
    
    def test_minute_grouping_accuracy(self):
        """Test that logs are correctly grouped by minute"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'line'})
        data = json.loads(response.content)
        
        # We created logs at 3 different minutes, so should have 3 data points
        self.assertEqual(len(data['data']), 3)
        
        # Verify minutes are in chronological order
        for i in range(len(data['data']) - 1):
            current_minute = data['data'][i]['minute']
            next_minute = data['data'][i + 1]['minute']
            self.assertLess(current_minute, next_minute, 
                          "Minutes should be in chronological order")
    
    def test_all_classifications_represented(self):
        """Test that all 7 classification classes are included in responses"""
        self.client.login(username='testuser', password='testpass123')
        
        # Line chart
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'line'})
        data = json.loads(response.content)
        
        # Every time point should have all 7 classes
        for time_point in data['data']:
            for i in range(7):
                self.assertIn(f'class_{i}', time_point)
        
        # Pie chart - should only include classes that have data
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'pie'})
        data = json.loads(response.content)
        
        # Should have 7 items (one for each classification with data)
        self.assertEqual(len(data['data']), 7)
    
    def test_data_type_consistency(self):
        """Test that all returned data types are consistent"""
        self.client.login(username='testuser', password='testpass123')
        
        # Line chart
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'line'})
        data = json.loads(response.content)
        
        for time_point in data['data']:
            # Minute should be string
            self.assertIsInstance(time_point['minute'], str)
            
            # All class counts should be integers
            for i in range(7):
                self.assertIsInstance(time_point[f'class_{i}'], int)
        
        # Pie chart
        response = self.client.get(reverse('analytics:api_chart_data'), {'type': 'pie'})
        data = json.loads(response.content)
        
        for item in data['data']:
            # classification_class should be int
            self.assertIsInstance(item['classification_class'], int)
            # classification_name should be string
            self.assertIsInstance(item['classification_name'], str)
            # count should be int
            self.assertIsInstance(item['count'], int)


class AnalyticsViewsTestCase(TestCase):
    """Test suite for analytics dashboard views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_analytics_dashboard_requires_login(self):
        """Test that analytics dashboard requires authentication"""
        response = self.client.get(reverse('analytics:analytics_dashboard'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_analytics_dashboard_authenticated(self):
        """Test that authenticated users can access analytics dashboard"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('analytics:analytics_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analytics/dashboard.html')
    
    def test_dashboard_contains_chart_elements(self):
        """Test that dashboard template contains required chart elements"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('analytics:analytics_dashboard'))
        content = response.content.decode('utf-8')
        
        # Check for chart canvases
        self.assertIn('volumeChart', content)
        self.assertIn('typeChart', content)
        
        # Check for refresh button
        self.assertIn('refreshAllCharts', content)
        
        # Check for Chart.js script
        self.assertIn('chart.js', content.lower())


def run_analytics_tests():
    """Helper function to run analytics tests"""
    import sys
    from django.core.management import execute_from_command_line
    
    sys.argv = ['manage.py', 'test', 'analytics.tests', '--verbosity=2']
    execute_from_command_line(sys.argv)
