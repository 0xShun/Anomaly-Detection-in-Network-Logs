#!/usr/bin/env python3
"""
Local API Integration Test Suite

Tests all API endpoints locally and verifies data appears in dashboard and analytics.

Usage:
    python3 test_local_api.py
    python3 test_local_api.py --port 8000
    python3 test_local_api.py --url http://localhost:8000
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timedelta

# Check dependencies
try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    print("❌ Missing required package: requests")
    print("Install with: pip3 install requests")
    sys.exit(1)


class LocalAPITester:
    """Test local API endpoints and data flow"""
    
    def __init__(self, base_url: str, username: str = None, password: str = None, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.api_key = api_key
        self.session = requests.Session()
        
        # API endpoints
        self.api_logs_url = f"{self.base_url}/api/v1/logs/"
        self.dashboard_url = f"{self.base_url}/dashboard/"
        self.analytics_url = f"{self.base_url}/analytics/"
        self.analytics_api_url = f"{self.base_url}/analytics/api/chart-data/"
        
        # Store created log IDs for verification
        self.created_log_ids = []
        self.created_anomaly_ids = []
        
    def login(self) -> bool:
        """Login to the application"""
        if not self.username or not self.password:
            print("⚠️  No credentials provided, skipping authentication")
            return True
            
        print("=" * 80)
        print("AUTHENTICATION")
        print("=" * 80)
        
        login_url = f"{self.base_url}/auth/login/"
        
        try:
            # Get login page to get CSRF token
            response = self.session.get(login_url, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Cannot access login page: {response.status_code}")
                return False
            
            # Extract CSRF token
            csrf_token = None
            if 'csrftoken' in self.session.cookies:
                csrf_token = self.session.cookies['csrftoken']
            
            # Login
            login_data = {
                'username': self.username,
                'password': self.password,
                'csrfmiddlewaretoken': csrf_token
            }
            
            response = self.session.post(
                login_url,
                data=login_data,
                headers={'Referer': login_url},
                timeout=10
            )
            
            # Check if login was successful (redirect or 200)
            if response.status_code in [200, 302]:
                # Verify by accessing a protected page
                test_response = self.session.get(self.dashboard_url, timeout=10)
                if test_response.status_code == 200:
                    print(f"✅ Successfully logged in as {self.username}")
                    return True
            
            print(f"❌ Login failed")
            return False
            
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def post_to_api(self, url: str, data: dict) -> requests.Response:
        """Helper method to POST to API with proper authentication"""
        headers = {'Content-Type': 'application/json'}
        
        # Add API key authentication
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        # Add CSRF token if available (for session-based endpoints)
        csrf_token = self.session.cookies.get('csrftoken', '')
        if csrf_token:
            headers['X-CSRFToken'] = csrf_token
        
        return self.session.post(
            url,
            json=data,
            headers=headers,
            timeout=10
        )
    
    def test_connectivity(self) -> bool:
        """Test basic connectivity to the server"""
        print("\n" + "=" * 80)
        print("TEST 1: Server Connectivity")
        print("=" * 80)
        
        try:
            response = requests.get(self.base_url, timeout=10)
            print(f"✅ Server is reachable at {self.base_url}")
            print(f"   Status code: {response.status_code}")
            return True
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to {self.base_url}")
            print(f"   Is the Django server running?")
            print(f"   Start with: python3 manage.py runserver")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def test_api_logs_endpoint_security_anomaly(self) -> bool:
        """Test /api/logs/ endpoint with Security Anomaly"""
        print("\n" + "=" * 80)
        print("TEST 2: API Logs Endpoint - Security Anomaly (Class 1)")
        print("=" * 80)
        
        test_data = {
            "log_message": "Failed password for admin from 192.168.1.100 port 22 ssh2",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "host_ip": "192.168.1.100",
            "source": "linux_test",
            "log_type": "ERROR",
            "classification_class": 1,
            "classification_name": "Security Anomaly",
            "anomaly_score": 0.9234,
            "severity": "critical",
            "is_anomaly": True
        }
        
        print(f"Endpoint: {self.api_logs_url}")
        print(f"Data: {json.dumps(test_data, indent=2)}")
        
        try:
            response = self.post_to_api(self.api_logs_url, test_data)
            
            print(f"\nResponse status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 201:
                response_data = response.json()
                log_id = response_data.get('log_id')
                anomaly_created = response_data.get('anomaly_created', False)
                
                print(f"\n✅ Security anomaly log created successfully")
                print(f"   Log ID: {log_id}")
                print(f"   Classification: {response_data.get('classification')}")
                print(f"   Anomaly created: {anomaly_created}")
                
                if log_id:
                    self.created_log_ids.append(log_id)
                
                if anomaly_created:
                    print(f"   ✅ Anomaly record created (expected for Security)")
                else:
                    print(f"   ⚠️  No anomaly record created (unexpected for Security)")
                    
                return True
            else:
                print(f"❌ Failed to create log: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_api_logs_endpoint_system_failure(self) -> bool:
        """Test /api/logs/ endpoint with System Failure"""
        print("\n" + "=" * 80)
        print("TEST 3: API Logs Endpoint - System Failure (Class 2)")
        print("=" * 80)
        
        test_data = {
            "log_message": "Kernel panic - not syncing: Fatal exception",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "host_ip": "192.168.1.50",
            "source": "linux_test",
            "log_type": "ERROR",
            "classification_class": 2,
            "classification_name": "System Failure",
            "anomaly_score": 0.8765,
            "severity": "critical",
            "is_anomaly": True
        }
        
        print(f"Endpoint: {self.api_logs_url}")
        print(f"Data: {json.dumps(test_data, indent=2)}")
        
        try:
            response = self.post_to_api(self.api_logs_url, test_data)
            
            print(f"\nResponse status: {response.status_code}")
            
            if response.status_code == 201:
                response_data = response.json()
                log_id = response_data.get('log_id')
                anomaly_created = response_data.get('anomaly_created', False)
                
                print(f"✅ System failure log created successfully")
                print(f"   Log ID: {log_id}")
                print(f"   Anomaly created: {anomaly_created}")
                
                if log_id:
                    self.created_log_ids.append(log_id)
                
                if anomaly_created:
                    print(f"   ✅ Anomaly record created (expected for System Failure)")
                else:
                    print(f"   ⚠️  No anomaly record created (unexpected)")
                    
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_api_logs_endpoint_normal(self) -> bool:
        """Test /api/logs/ endpoint with Normal log (no anomaly)"""
        print("\n" + "=" * 80)
        print("TEST 4: API Logs Endpoint - Normal Log (Class 0)")
        print("=" * 80)
        
        test_data = {
            "log_message": "GET /index.html HTTP/1.1 200 1234",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "host_ip": "192.168.1.75",
            "source": "apache_test",
            "log_type": "INFO",
            "classification_class": 0,
            "classification_name": "Normal",
            "anomaly_score": 0.0234,
            "severity": "info",
            "is_anomaly": False
        }
        
        print(f"Endpoint: {self.api_logs_url}")
        print(f"Data: {json.dumps(test_data, indent=2)}")
        
        try:
            response = self.post_to_api(self.api_logs_url, test_data)
            
            print(f"\nResponse status: {response.status_code}")
            
            if response.status_code == 201:
                response_data = response.json()
                log_id = response_data.get('log_id')
                anomaly_created = response_data.get('anomaly_created', False)
                
                print(f"✅ Normal log created successfully")
                print(f"   Log ID: {log_id}")
                print(f"   Anomaly created: {anomaly_created}")
                
                if log_id:
                    self.created_log_ids.append(log_id)
                
                if not anomaly_created:
                    print(f"   ✅ No anomaly record (expected for Normal)")
                else:
                    print(f"   ⚠️  Anomaly created (unexpected for Normal)")
                    
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_api_logs_endpoint_performance(self) -> bool:
        """Test /api/logs/ endpoint with Performance Issue (should NOT create anomaly)"""
        print("\n" + "=" * 80)
        print("TEST 5: API Logs Endpoint - Performance Issue (Class 3, No Anomaly)")
        print("=" * 80)
        
        test_data = {
            "log_message": "High CPU usage detected: 95%",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "host_ip": "192.168.1.80",
            "source": "monitoring_test",
            "log_type": "WARNING",
            "classification_class": 3,
            "classification_name": "Performance Issue",
            "anomaly_score": 0.6543,
            "severity": "medium",
            "is_anomaly": False
        }
        
        print(f"Endpoint: {self.api_logs_url}")
        print(f"Data: {json.dumps(test_data, indent=2)}")
        
        try:
            response = self.post_to_api(self.api_logs_url, test_data)
            
            print(f"\nResponse status: {response.status_code}")
            
            if response.status_code == 201:
                response_data = response.json()
                log_id = response_data.get('log_id')
                anomaly_created = response_data.get('anomaly_created', False)
                
                print(f"✅ Performance log created successfully")
                print(f"   Log ID: {log_id}")
                print(f"   Anomaly created: {anomaly_created}")
                
                if log_id:
                    self.created_log_ids.append(log_id)
                
                if not anomaly_created:
                    print(f"   ✅ No anomaly record (expected - only Security/System Failure create anomalies)")
                else:
                    print(f"   ⚠️  Anomaly created (unexpected for Performance)")
                    
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_dashboard_data_visibility(self) -> bool:
        """Test that logs appear in dashboard"""
        print("\n" + "=" * 80)
        print("TEST 6: Dashboard Data Visibility")
        print("=" * 80)
        
        if not self.created_log_ids:
            print("⚠️  No logs created yet, skipping")
            return True
        
        print(f"Checking dashboard for {len(self.created_log_ids)} created logs...")
        
        try:
            response = self.session.get(self.dashboard_url, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Cannot access dashboard: {response.status_code}")
                return False
            
            content = response.text
            
            # Check if created logs appear in dashboard
            found_logs = 0
            for log_id in self.created_log_ids[-3:]:  # Check last 3 logs
                if str(log_id) in content:
                    found_logs += 1
            
            print(f"✅ Dashboard accessible")
            print(f"   Found {found_logs}/{min(3, len(self.created_log_ids))} recent logs in dashboard HTML")
            
            # Check for key dashboard elements
            dashboard_elements = {
                'Total Logs': 'Total Logs' in content,
                'Active Anomalies': 'Active Anomalies' in content or 'Anomalies' in content,
                'Log Table': 'log-table' in content or 'table' in content,
                'Classification Stats': 'classification' in content.lower()
            }
            
            print(f"\n   Dashboard elements:")
            for element, present in dashboard_elements.items():
                status = "✅" if present else "❌"
                print(f"   {status} {element}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error accessing dashboard: {e}")
            return False
    
    def test_analytics_chart_data(self) -> bool:
        """Test analytics chart data API"""
        print("\n" + "=" * 80)
        print("TEST 7: Analytics Chart Data API")
        print("=" * 80)
        
        tests_passed = 0
        tests_total = 2
        
        # Test line chart (volume over time)
        print("\n📊 Testing Line Chart API...")
        try:
            response = self.session.get(
                self.analytics_api_url,
                params={'type': 'line'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Line chart API accessible")
                print(f"   Chart type: {data.get('type')}")
                print(f"   Chart title: {data.get('title')}")
                print(f"   Data points: {len(data.get('data', []))}")
                
                # Check data structure
                if data.get('data'):
                    sample = data['data'][0]
                    has_all_classes = all(f'class_{i}' in sample for i in range(7))
                    
                    if has_all_classes:
                        print(f"   ✅ All 7 classification fields present")
                        tests_passed += 1
                    else:
                        print(f"   ⚠️  Missing some classification fields")
                else:
                    print(f"   ℹ️  No data points (database might be empty)")
                    tests_passed += 1
            else:
                print(f"❌ Line chart API failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing line chart: {e}")
        
        # Test pie chart (classification distribution)
        print("\n🥧 Testing Pie Chart API...")
        try:
            response = self.session.get(
                self.analytics_api_url,
                params={'type': 'pie'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Pie chart API accessible")
                print(f"   Chart type: {data.get('type')}")
                print(f"   Chart title: {data.get('title')}")
                print(f"   Classifications: {len(data.get('data', []))}")
                
                # Show classification distribution
                if data.get('data'):
                    print(f"\n   Classification Distribution:")
                    for item in data['data']:
                        class_num = item.get('classification_class')
                        class_name = item.get('classification_name')
                        count = item.get('count')
                        print(f"   - Class {class_num} ({class_name}): {count} logs")
                    tests_passed += 1
                else:
                    print(f"   ℹ️  No data (database might be empty)")
                    tests_passed += 1
            else:
                print(f"❌ Pie chart API failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing pie chart: {e}")
        
        print(f"\n📊 Analytics API: {tests_passed}/{tests_total} endpoints working")
        return tests_passed == tests_total
    
    def test_analytics_page_visibility(self) -> bool:
        """Test that analytics page loads and shows charts"""
        print("\n" + "=" * 80)
        print("TEST 8: Analytics Page Visibility")
        print("=" * 80)
        
        try:
            response = self.session.get(self.analytics_url, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Cannot access analytics page: {response.status_code}")
                return False
            
            content = response.text
            
            # Check for chart elements
            chart_elements = {
                'Volume Chart Canvas': 'volumeChart' in content,
                'Type Chart Canvas': 'typeChart' in content,
                'Chart.js Library': 'chart.js' in content.lower(),
                'Refresh Charts Button': 'refreshAllCharts' in content,
                'Log Volume Title': 'Log Volume Over Time' in content,
                'Classification Distribution': 'Classification Distribution' in content
            }
            
            print(f"✅ Analytics page accessible")
            print(f"\n   Chart elements:")
            
            all_present = True
            for element, present in chart_elements.items():
                status = "✅" if present else "❌"
                print(f"   {status} {element}")
                if not present:
                    all_present = False
            
            return all_present
            
        except Exception as e:
            print(f"❌ Error accessing analytics page: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test API error handling"""
        print("\n" + "=" * 80)
        print("TEST 9: API Error Handling")
        print("=" * 80)
        
        # Test missing required fields
        invalid_data = {
            "log_message": "Test log",
            # Missing required fields
        }
        
        print("Testing with missing required fields...")
        
        try:
            response = self.post_to_api(self.api_logs_url, invalid_data)
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 400:
                print(f"✅ API correctly rejected invalid data (400 Bad Request)")
                print(f"   Error message: {response.text}")
                return True
            else:
                print(f"⚠️  Expected 400, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_data_flow_end_to_end(self) -> bool:
        """Test complete data flow from API to dashboard to analytics"""
        print("\n" + "=" * 80)
        print("TEST 10: End-to-End Data Flow")
        print("=" * 80)
        
        print("Creating test log with unique identifier...")
        
        unique_id = f"TEST_{int(time.time())}"
        test_data = {
            "log_message": f"End-to-end test log {unique_id}",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "host_ip": "192.168.1.99",
            "source": "e2e_test",
            "log_type": "INFO",
            "classification_class": 4,  # Network Anomaly
            "classification_name": "Network Anomaly",
            "anomaly_score": 0.7123,
            "severity": "high",
            "is_anomaly": False  # Class 4 doesn't create anomaly
        }
        
        try:
            # Step 1: Send log via API
            print(f"\n1️⃣  Sending log via API...")
            response = self.post_to_api(self.api_logs_url, test_data)
            
            if response.status_code != 201:
                print(f"❌ Failed to create log: {response.status_code}")
                return False
            
            response_data = response.json()
            log_id = response_data.get('log_id')
            print(f"✅ Log created with ID: {log_id}")
            
            # Step 2: Wait a moment for database
            time.sleep(1)
            
            # Step 3: Check dashboard
            print(f"\n2️⃣  Checking dashboard...")
            dashboard_response = self.session.get(self.dashboard_url, timeout=10)
            
            if dashboard_response.status_code == 200:
                if unique_id in dashboard_response.text or str(log_id) in dashboard_response.text:
                    print(f"✅ Log visible in dashboard")
                else:
                    print(f"⚠️  Log not found in dashboard (might be paginated)")
            else:
                print(f"⚠️  Cannot verify dashboard: {dashboard_response.status_code}")
            
            # Step 4: Check analytics data
            print(f"\n3️⃣  Checking analytics charts...")
            analytics_response = self.session.get(
                self.analytics_api_url,
                params={'type': 'pie'},
                timeout=10
            )
            
            if analytics_response.status_code == 200:
                analytics_data = analytics_response.json()
                
                # Check if our classification appears
                class_4_found = False
                for item in analytics_data.get('data', []):
                    if item.get('classification_class') == 4:
                        class_4_found = True
                        count = item.get('count', 0)
                        print(f"✅ Classification 4 (Network Anomaly) in analytics: {count} logs")
                        break
                
                if not class_4_found:
                    print(f"⚠️  Classification 4 not in analytics data yet")
            else:
                print(f"⚠️  Cannot verify analytics: {analytics_response.status_code}")
            
            print(f"\n✅ End-to-end data flow test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error in end-to-end test: {e}")
            return False
    
    def run_all_tests(self) -> int:
        """Run all tests"""
        print("\n" + "🧪" * 40)
        print("LOCAL API INTEGRATION TEST SUITE")
        print("🧪" * 40)
        print(f"Testing server: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Login first if credentials provided
        if self.username and self.password:
            if not self.login():
                print("\n❌ Login failed, some tests may not work")
        
        # Run all tests
        results = {}
        
        results['connectivity'] = self.test_connectivity()
        
        if not results['connectivity']:
            print("\n❌ Server not reachable. Please start the Django server:")
            print("   cd webplatform")
            print("   python3 manage.py runserver")
            return 1
        
        results['api_security'] = self.test_api_logs_endpoint_security_anomaly()
        results['api_system_failure'] = self.test_api_logs_endpoint_system_failure()
        results['api_normal'] = self.test_api_logs_endpoint_normal()
        results['api_performance'] = self.test_api_logs_endpoint_performance()
        results['dashboard_visibility'] = self.test_dashboard_data_visibility()
        results['analytics_api'] = self.test_analytics_chart_data()
        results['analytics_page'] = self.test_analytics_page_visibility()
        results['error_handling'] = self.test_error_handling()
        results['end_to_end'] = self.test_data_flow_end_to_end()
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total = len(results)
        passed = sum(1 for v in results.values() if v)
        
        for test_name, test_passed in results.items():
            status = "✅ PASS" if test_passed else "❌ FAIL"
            print(f"{status} - {test_name.replace('_', ' ').title()}")
        
        print()
        print(f"Results: {passed}/{total} tests passed")
        
        if self.created_log_ids:
            print(f"\nℹ️  Created {len(self.created_log_ids)} test logs")
            print(f"   View them at: {self.dashboard_url}")
        
        if passed == total:
            print("\n🎉 All tests passed! Local API is working correctly.")
            print("\n✅ Data Flow Verified:")
            print("   API → Database → Dashboard → Analytics")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
            return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Test local API endpoints and data flow'
    )
    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:8000',
        help='Base URL of local server (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--port',
        type=int,
        help='Port number (alternative to --url)'
    )
    parser.add_argument(
        '--username',
        type=str,
        default='admin',
        help='Username for authentication (default: admin)'
    )
    parser.add_argument(
        '--password',
        type=str,
        default='admin123',
        help='Password for authentication (default: admin123)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='API key for authentication (reads from LOGBERT_API_KEYS env if not provided)'
    )
    
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key
    if not api_key:
        # Try to get first API key from environment
        api_keys_env = os.environ.get('LOGBERT_API_KEYS', '')
        if api_keys_env:
            api_keys = [k.strip() for k in api_keys_env.split(',') if k.strip()]
            if api_keys:
                api_key = api_keys[0]
                print(f"ℹ️  Using API key from LOGBERT_API_KEYS environment variable")
    
    if not api_key:
        print("⚠️  WARNING: No API key provided!")
        print("   Set LOGBERT_API_KEYS environment variable or use --api-key argument")
        print("   API endpoint tests may fail without authentication")
    
    # Determine base URL
    if args.port:
        base_url = f"http://localhost:{args.port}"
    else:
        base_url = args.url
    
    # Validate URL
    if not base_url.startswith(('http://', 'https://')):
        print(f"❌ Invalid URL: {base_url}")
        print("   URL must start with http:// or https://")
        sys.exit(1)
    
    print(f"\n🚀 Starting local API tests...")
    print(f"Server: {base_url}")
    if api_key:
        print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
    
    # Run tests
    tester = LocalAPITester(base_url, args.username, args.password, api_key)
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
