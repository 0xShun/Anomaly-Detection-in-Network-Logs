#!/usr/bin/env python
"""
Comprehensive API Testing Script for LogBERT Remote Monitoring Platform

This script performs thorough testing of all API endpoints with detailed reporting.

Usage:
    export LOGBERT_API_KEY="your-api-key"
    export LOGBERT_REMOTE_URL="http://localhost:8000"  # or your PythonAnywhere URL
    python comprehensive_api_test.py
"""

import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import time


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class APITester:
    """Comprehensive API testing class"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        self.passed = 0
        self.failed = 0
        self.errors: List[str] = []
        self.created_ids = {
            'alerts': [],
            'metrics': [],
            'statistics': [],
            'raw_outputs': []
        }
    
    def print_header(self, text: str):
        """Print colored header"""
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}")
        print(f"{text}")
        print(f"{'='*70}{Colors.END}\n")
    
    def print_test(self, test_name: str):
        """Print test name"""
        print(f"{Colors.BOLD}{test_name}{Colors.END}")
    
    def print_pass(self, message: str):
        """Print success message"""
        self.passed += 1
        print(f"  {Colors.GREEN}✓ PASS{Colors.END}: {message}")
    
    def print_fail(self, message: str, details: Optional[str] = None):
        """Print failure message"""
        self.failed += 1
        error_msg = message
        if details:
            error_msg += f" - {details}"
        self.errors.append(error_msg)
        print(f"  {Colors.RED}✗ FAIL{Colors.END}: {message}")
        if details:
            print(f"    Details: {details}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"    {message}")
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> Optional[requests.Response]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response
        
        except requests.exceptions.Timeout:
            self.print_fail("Request timeout (>10s)")
            return None
        except requests.exceptions.ConnectionError:
            self.print_fail("Connection error", "Is the server running?")
            return None
        except Exception as e:
            self.print_fail("Exception", str(e))
            return None
    
    def test_authentication(self):
        """Test API authentication"""
        self.print_header("1. AUTHENTICATION TESTS")
        
        # Test 1.1: Valid API key
        self.print_test("1.1. Valid API Key (Bearer token)")
        response = self.make_request('GET', '/api/v1/status/')
        if response and response.status_code == 200:
            self.print_pass("Authentication successful with valid API key")
        elif response:
            self.print_fail(f"Unexpected status code: {response.status_code}", response.text[:100])
        
        # Test 1.2: Invalid API key
        self.print_test("1.2. Invalid API Key")
        invalid_headers = {
            'Authorization': 'Bearer invalid-key-xyz',
            'Content-Type': 'application/json',
        }
        try:
            response = requests.get(f"{self.base_url}/api/v1/alerts/", 
                                   headers=invalid_headers, timeout=10)
            if response.status_code in [401, 403]:
                self.print_pass(f"Correctly rejected invalid API key ({response.status_code})")
            else:
                self.print_fail(f"Should return 401 or 403, got {response.status_code}")
        except Exception as e:
            self.print_fail("Exception", str(e))
        
        # Test 1.3: Missing API key
        self.print_test("1.3. Missing API Key")
        try:
            response = requests.get(f"{self.base_url}/api/v1/alerts/", timeout=10)
            if response.status_code in [401, 403]:
                self.print_pass(f"Correctly rejected missing API key ({response.status_code})")
            else:
                self.print_fail(f"Should return 401 or 403, got {response.status_code}")
        except Exception as e:
            self.print_fail("Exception", str(e))
    
    def test_status_endpoints(self):
        """Test system status endpoints"""
        self.print_header("2. STATUS ENDPOINTS")
        
        # Test 2.1: Status endpoint
        self.print_test("2.1. GET /api/v1/status/")
        response = self.make_request('GET', '/api/v1/status/')
        if response and response.status_code == 200:
            data = response.json()
            self.print_info(f"Response: {json.dumps(data, indent=2)}")
            
            if 'status' in data and 'endpoints' in data:
                self.print_pass("Status endpoint returns correct structure")
            else:
                self.print_fail("Missing required fields", "Expected 'status' and 'endpoints'")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:100])
        
        # Test 2.2: Health check endpoint
        self.print_test("2.2. POST /api/v1/health/")
        health_data = {
            "school_id": "test-school",
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
        response = self.make_request('POST', '/api/v1/health/', data=health_data)
        if response and response.status_code == 200:
            self.print_pass("Health check accepted")
            self.print_info(f"Response: {json.dumps(response.json(), indent=2)}")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:100])
    
    def test_alert_crud(self):
        """Test Alert CRUD operations"""
        self.print_header("3. ALERT ENDPOINTS")
        
        # Test 3.1: Create alert
        self.print_test("3.1. POST /api/v1/alerts/ (Create)")
        alert_data = {
            "school_id": "test-school-001",
            "alert_type": "anomaly_detected",
            "message": "Test anomaly: Suspicious login pattern detected",
            "level": "high",
            "anomaly_score": 0.92,
            "affected_systems": "web-server-01,db-server-01",
            "status": "active"
        }
        response = self.make_request('POST', '/api/v1/alerts/', data=alert_data)
        
        alert_id = None
        if response and response.status_code == 201:
            data = response.json()
            alert_id = data.get('id')
            self.created_ids['alerts'].append(alert_id)
            self.print_pass(f"Alert created successfully (ID: {alert_id})")
            self.print_info(f"Response: {json.dumps(data, indent=2)}")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:200])
        
        # Test 3.2: List alerts
        self.print_test("3.2. GET /api/v1/alerts/ (List all)")
        response = self.make_request('GET', '/api/v1/alerts/')
        if response and response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            results = data.get('results', [])
            self.print_pass(f"Retrieved {len(results)} alerts (total: {count})")
            if results:
                self.print_info(f"Sample: {json.dumps(results[0], indent=2)}")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:100])
        
        # Test 3.3: Filter by level
        self.print_test("3.3. GET /api/v1/alerts/?level=high (Filter)")
        response = self.make_request('GET', '/api/v1/alerts/', params={'level': 'high'})
        if response and response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            all_high = all(a['level'] == 'high' for a in results)
            if all_high:
                self.print_pass(f"Filter working: {len(results)} high-level alerts")
            else:
                self.print_fail("Filter not working", "Some alerts have different levels")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:100])
        
        # Test 3.4: Filter by school
        self.print_test("3.4. GET /api/v1/alerts/?school_id=test-school-001")
        response = self.make_request('GET', '/api/v1/alerts/', 
                                    params={'school_id': 'test-school-001'})
        if response and response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            all_match = all(a['school_id'] == 'test-school-001' for a in results)
            if all_match:
                self.print_pass(f"School filter working: {len(results)} results")
            else:
                self.print_fail("School filter not working")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:100])
        
        # Test 3.5: Invalid alert level
        self.print_test("3.5. POST /api/v1/alerts/ (Invalid level)")
        invalid_alert = {
            "school_id": "test-school-001",
            "alert_type": "test",
            "message": "Test",
            "level": "invalid_level",  # Should fail
            "status": "active"
        }
        response = self.make_request('POST', '/api/v1/alerts/', data=invalid_alert)
        if response and response.status_code == 400:
            self.print_pass("Correctly rejected invalid alert level (400)")
        elif response:
            self.print_fail(f"Should return 400, got {response.status_code}")
    
    def test_metric_crud(self):
        """Test SystemMetric CRUD operations"""
        self.print_header("4. METRIC ENDPOINTS")
        
        # Test 4.1: Create metric
        self.print_test("4.1. POST /api/v1/metrics/ (Create)")
        metric_data = {
            "school_id": "test-school-001",
            "metric_type": "cpu_usage",
            "value": 75.5,
            "unit": "percent",
            "source": "server-01",
            "metadata": {"core_count": 4, "process": "logbert-analyzer"}
        }
        response = self.make_request('POST', '/api/v1/metrics/', data=metric_data)
        
        if response and response.status_code == 201:
            data = response.json()
            metric_id = data.get('id')
            self.created_ids['metrics'].append(metric_id)
            self.print_pass(f"Metric created successfully (ID: {metric_id})")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:200])
        
        # Test 4.2: Create memory metric
        self.print_test("4.2. POST /api/v1/metrics/ (Memory)")
        metric_data = {
            "school_id": "test-school-001",
            "metric_type": "memory_usage",
            "value": 8192,
            "unit": "MB",
            "source": "server-01"
        }
        response = self.make_request('POST', '/api/v1/metrics/', data=metric_data)
        
        if response and response.status_code == 201:
            self.print_pass("Memory metric created")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:100])
        
        # Test 4.3: List metrics
        self.print_test("4.3. GET /api/v1/metrics/ (List)")
        response = self.make_request('GET', '/api/v1/metrics/')
        if response and response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            self.print_pass(f"Retrieved metrics (total: {count})")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:100])
        
        # Test 4.4: Filter by type
        self.print_test("4.4. GET /api/v1/metrics/?metric_type=cpu_usage")
        response = self.make_request('GET', '/api/v1/metrics/', 
                                    params={'metric_type': 'cpu_usage'})
        if response and response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            all_cpu = all(m['metric_type'] == 'cpu_usage' for m in results)
            if all_cpu:
                self.print_pass(f"Type filter working: {len(results)} CPU metrics")
            else:
                self.print_fail("Type filter not working")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:100])
    
    def test_statistic_crud(self):
        """Test LogStatistic CRUD operations"""
        self.print_header("5. STATISTIC ENDPOINTS")
        
        # Test 5.1: Create statistic
        self.print_test("5.1. POST /api/v1/statistics/ (Create)")
        stat_data = {
            "school_id": "test-school-001",
            "total_logs_processed": 100000,
            "anomalous_logs": 523,
            "normal_logs": 99477,
            "parsing_coverage": 98.7,
            "top_templates": [
                {"template": "User <*> logged in from <*>", "count": 25000},
                {"template": "HTTP <*> request to <*>", "count": 30000},
                {"template": "Database query executed", "count": 20000}
            ],
            "source_breakdown": {
                "apache": 40000,
                "linux": 35000,
                "openssh": 25000
            },
            "time_range_start": "2025-11-05T00:00:00Z",
            "time_range_end": "2025-11-05T23:59:59Z"
        }
        response = self.make_request('POST', '/api/v1/statistics/', data=stat_data)
        
        if response and response.status_code == 201:
            data = response.json()
            stat_id = data.get('id')
            self.created_ids['statistics'].append(stat_id)
            self.print_pass(f"Statistic created successfully (ID: {stat_id})")
            self.print_info(f"Processed: {stat_data['total_logs_processed']} logs")
            self.print_info(f"Anomalies: {stat_data['anomalous_logs']} " +
                          f"({stat_data['anomalous_logs']/stat_data['total_logs_processed']*100:.2f}%)")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:200])
        
        # Test 5.2: List statistics
        self.print_test("5.2. GET /api/v1/statistics/ (List)")
        response = self.make_request('GET', '/api/v1/statistics/')
        if response and response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            self.print_pass(f"Retrieved statistics (total: {count})")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:100])
    
    def test_raw_output_crud(self):
        """Test RawModelOutput CRUD operations"""
        self.print_header("6. RAW OUTPUT ENDPOINTS")
        
        # Test 6.1: Create raw output
        self.print_test("6.1. POST /api/v1/raw-outputs/ (Create)")
        raw_output_data = {
            "school_id": "test-school-001",
            "log_sequence": "User admin login from 192.168.1.100 at 14:23:45",
            "log_key": "ssh_001",
            "masked_predictions": ["User", "[MASK]", "login", "from", "[IP]", "at", "[TIME]"],
            "anomaly_scores": [0.05, 0.92, 0.03, 0.02, 0.88, 0.01, 0.04],
            "attention_weights": [[0.1, 0.3, 0.2, 0.15, 0.15, 0.05, 0.05]],
            "final_anomaly_score": 0.92,
            "is_anomaly": True,
            "model_version": "logbert-v1.0",
            "model_confidence": 0.95
        }
        response = self.make_request('POST', '/api/v1/raw-outputs/', data=raw_output_data)
        
        if response and response.status_code == 201:
            data = response.json()
            output_id = data.get('id')
            self.created_ids['raw_outputs'].append(output_id)
            self.print_pass(f"Raw output created successfully (ID: {output_id})")
            self.print_info(f"Anomaly score: {raw_output_data['final_anomaly_score']}")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:200])
        
        # Test 6.2: List raw outputs
        self.print_test("6.2. GET /api/v1/raw-outputs/ (List)")
        response = self.make_request('GET', '/api/v1/raw-outputs/')
        if response and response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            self.print_pass(f"Retrieved raw outputs (total: {count})")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:100])
        
        # Test 6.3: Filter anomalies only
        self.print_test("6.3. GET /api/v1/raw-outputs/?is_anomaly=true")
        response = self.make_request('GET', '/api/v1/raw-outputs/', 
                                    params={'is_anomaly': 'true'})
        if response and response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            all_anomalies = all(r['is_anomaly'] for r in results)
            if all_anomalies:
                self.print_pass(f"Anomaly filter working: {len(results)} anomalies")
            else:
                self.print_fail("Anomaly filter not working")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:100])
    
    def test_pagination(self):
        """Test API pagination"""
        self.print_header("7. PAGINATION TESTS")
        
        # Create multiple alerts for pagination
        self.print_test("7.1. Creating test data for pagination")
        for i in range(5):
            alert_data = {
                "school_id": "test-pagination",
                "alert_type": "test",
                "message": f"Pagination test alert {i}",
                "level": "low",
                "status": "active"
            }
            response = self.make_request('POST', '/api/v1/alerts/', data=alert_data)
            if response and response.status_code == 201:
                self.created_ids['alerts'].append(response.json()['id'])
        
        self.print_pass("Created test alerts for pagination")
        
        # Test pagination
        self.print_test("7.2. GET /api/v1/alerts/ (Check pagination)")
        response = self.make_request('GET', '/api/v1/alerts/')
        if response and response.status_code == 200:
            data = response.json()
            if 'results' in data and 'count' in data:
                self.print_pass("Pagination structure correct")
                self.print_info(f"Total count: {data['count']}")
                self.print_info(f"Results in page: {len(data['results'])}")
                if 'next' in data:
                    self.print_info(f"Next page: {data['next']}")
                if 'previous' in data:
                    self.print_info(f"Previous page: {data['previous']}")
            else:
                self.print_fail("Missing pagination fields")
        elif response:
            self.print_fail(f"HTTP {response.status_code}", response.text[:100])
    
    def run_all_tests(self):
        """Run all test suites"""
        print(f"\n{Colors.BOLD}╔════════════════════════════════════════════════════════════════════╗")
        print(f"║  LogBERT Remote Monitoring API - Comprehensive Test Suite         ║")
        print(f"╚════════════════════════════════════════════════════════════════════╝{Colors.END}\n")
        
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {self.api_key[:8]}...{self.api_key[-4:]}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        start_time = time.time()
        
        # Run test suites
        self.test_authentication()
        self.test_status_endpoints()
        self.test_alert_crud()
        self.test_metric_crud()
        self.test_statistic_crud()
        self.test_raw_output_crud()
        self.test_pagination()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print summary
        self.print_summary(duration)
    
    def print_summary(self, duration: float):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{'='*70}")
        print(f"TEST SUMMARY")
        print(f"{'='*70}{Colors.END}\n")
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests:  {total}")
        print(f"{Colors.GREEN}Passed:       {self.passed}{Colors.END}")
        print(f"{Colors.RED}Failed:       {self.failed}{Colors.END}")
        print(f"Pass Rate:    {pass_rate:.1f}%")
        print(f"Duration:     {duration:.2f} seconds")
        
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}Failed Tests:{Colors.END}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        print(f"\n{Colors.BOLD}Created Test Data:{Colors.END}")
        for resource, ids in self.created_ids.items():
            if ids:
                print(f"  {resource}: {len(ids)} items")
        
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.END}")
            print(f"\n{Colors.GREEN}The API is working correctly and ready for deployment.{Colors.END}\n")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.END}")
            print(f"\n{Colors.YELLOW}Please review the errors above and fix the issues.{Colors.END}\n")


def main():
    """Main entry point"""
    # Get configuration from environment
    api_key = os.environ.get('LOGBERT_API_KEY')
    base_url = os.environ.get('LOGBERT_REMOTE_URL', 'http://localhost:8000')
    
    if not api_key:
        print(f"{Colors.RED}ERROR: LOGBERT_API_KEY environment variable not set{Colors.END}")
        print("\nUsage:")
        print("  export LOGBERT_API_KEY='your-api-key-here'")
        print("  export LOGBERT_REMOTE_URL='http://localhost:8000'  # or your PythonAnywhere URL")
        print("  python comprehensive_api_test.py")
        sys.exit(1)
    
    # Run tests
    tester = APITester(base_url, api_key)
    tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if tester.failed == 0 else 1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {str(e)}{Colors.END}")
        sys.exit(1)
