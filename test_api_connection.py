#!/usr/bin/env python3
"""
Test API Connection to PythonAnywhere

This script tests the API endpoint to ensure it's working correctly.

Usage:
    python3 test_api_connection.py --api-url https://yoursite.pythonanywhere.com
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Check dependencies
try:
    import requests
except ImportError:
    print("❌ Missing required package: requests")
    print("Install with: pip3 install requests")
    sys.exit(1)


class APIConnectionTester:
    """Test API connectivity and functionality"""
    
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip('/') + '/api/logs/'
        self.base_url = api_url.rstrip('/')
        
    def test_connectivity(self) -> bool:
        """Test basic connectivity to the API"""
        print("=" * 80)
        print("TEST 1: Basic Connectivity")
        print("=" * 80)
        
        try:
            response = requests.get(self.base_url, timeout=10)
            print(f"✅ Server is reachable")
            print(f"   Status code: {response.status_code}")
            return True
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to {self.base_url}")
            print(f"   Make sure the server is running and the URL is correct")
            return False
        except requests.exceptions.Timeout:
            print(f"❌ Connection timeout")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_send_sample_log(self) -> bool:
        """Test sending a sample log"""
        print("\n" + "=" * 80)
        print("TEST 2: Send Sample Log (Security Anomaly)")
        print("=" * 80)
        
        sample_data = {
            "log_message": "Failed password for admin from 192.168.1.100 port 22 ssh2",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "host_ip": "192.168.1.100",
            "source": "linux",
            "log_type": "syslog",
            "classification_class": 1,
            "classification_name": "Security Anomaly",
            "anomaly_score": 0.8543,
            "severity": "critical",
            "is_anomaly": True
        }
        
        print(f"Sending to: {self.api_url}")
        print(f"Data: {json.dumps(sample_data, indent=2)}")
        print()
        
        try:
            response = requests.post(
                self.api_url,
                json=sample_data,
                timeout=10
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 201:
                print("✅ Sample log sent successfully")
                response_data = response.json()
                log_id = response_data.get('log_id')
                if log_id:
                    print(f"   Log ID: {log_id}")
                    print(f"   Classification: {response_data.get('classification')}")
                    print(f"   Anomaly created: {response_data.get('anomaly_created')}")
                return True
            else:
                print(f"❌ Failed to send log")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending sample log: {e}")
            return False
    
    def test_send_normal_log(self) -> bool:
        """Test sending a normal log (should not create anomaly)"""
        print("\n" + "=" * 80)
        print("TEST 3: Send Normal Log (No Anomaly)")
        print("=" * 80)
        
        sample_data = {
            "log_message": "GET /index.html HTTP/1.1 200 1234",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "host_ip": "192.168.1.50",
            "source": "apache",
            "log_type": "apache",
            "classification_class": 0,
            "classification_name": "Normal",
            "anomaly_score": 0.0543,
            "severity": "info",
            "is_anomaly": False
        }
        
        print(f"Sending to: {self.api_url}")
        print(f"Data: {json.dumps(sample_data, indent=2)}")
        print()
        
        try:
            response = requests.post(
                self.api_url,
                json=sample_data,
                timeout=10
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 201:
                response_data = response.json()
                anomaly_created = response_data.get('anomaly_created', False)
                
                if not anomaly_created:
                    print("✅ Normal log sent successfully (no anomaly created)")
                    print(f"   Log ID: {response_data.get('log_id')}")
                    print(f"   Classification: {response_data.get('classification')}")
                    return True
                else:
                    print("⚠️  Log sent but anomaly was created (unexpected)")
                    return False
            else:
                print(f"❌ Failed to send log")
                return False
                
        except Exception as e:
            print(f"❌ Error sending normal log: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling with invalid data"""
        print("\n" + "=" * 80)
        print("TEST 4: Error Handling (Missing Required Fields)")
        print("=" * 80)
        
        # Missing required fields
        invalid_data = {
            "log_message": "Test log",
            # Missing timestamp, classification_class, etc.
        }
        
        print(f"Sending invalid data: {json.dumps(invalid_data, indent=2)}")
        print()
        
        try:
            response = requests.post(
                self.api_url,
                json=invalid_data,
                timeout=10
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 400:
                print("✅ API correctly rejected invalid data")
                return True
            else:
                print(f"⚠️  Expected 400 error, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing error handling: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "🧪 API CONNECTION TEST SUITE")
        print("=" * 80)
        print(f"Testing API at: {self.api_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        results = {
            'connectivity': self.test_connectivity(),
            'send_sample': self.test_send_sample_log(),
            'send_normal': self.test_send_normal_log(),
            'error_handling': self.test_error_handling()
        }
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total = len(results)
        passed = sum(1 for v in results.values() if v)
        
        for test_name, passed_test in results.items():
            status = "✅ PASS" if passed_test else "❌ FAIL"
            print(f"{status} - {test_name.replace('_', ' ').title()}")
        
        print()
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed! API is ready for demo.")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please fix before demo.")
            return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Test API connection to PythonAnywhere'
    )
    parser.add_argument(
        '--api-url',
        type=str,
        default=os.getenv('API_URL', ''),
        help='PythonAnywhere API URL (e.g., https://yoursite.pythonanywhere.com)'
    )
    
    args = parser.parse_args()
    
    # Validate API URL
    if not args.api_url:
        print("❌ API URL is required!")
        print("   Use --api-url or set API_URL environment variable")
        print("   Example: python3 test_api_connection.py --api-url https://yoursite.pythonanywhere.com")
        sys.exit(1)
    
    # Validate URL format
    if not args.api_url.startswith(('http://', 'https://')):
        print(f"❌ Invalid API URL: {args.api_url}")
        print("   URL must start with http:// or https://")
        sys.exit(1)
    
    # Run tests
    tester = APIConnectionTester(args.api_url)
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
