#!/usr/bin/env python3
"""
Quick test script for threat intelligence integration.
Tests the unified lookup with a known IP address.
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/home/shun/Desktop/logbert/webplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webplatform.settings')
django.setup()

from dashboard.threat_intel_utils import unified_threat_lookup

def test_threat_intelligence():
    """Test threat intelligence lookup with a sample IP"""
    
    # Test with Google's public DNS (should be clean)
    test_ip = "8.8.8.8"
    
    print(f"🔍 Testing Unified Threat Intelligence Lookup")
    print(f"=" * 60)
    print(f"Target IP: {test_ip}")
    print(f"=" * 60)
    print()
    
    print("⏳ Querying VirusTotal, AbuseIPDB, and Shodan...")
    print()
    
    try:
        results = unified_threat_lookup(test_ip)
        
        if results.get('error'):
            print(f"❌ Error: {results['error']}")
            return
        
        print(f"✅ Lookup successful!")
        print(f"📦 Cached: {results.get('cached', False)}")
        if results.get('cached'):
            print(f"📅 Cache age: {results.get('cache_age', 0)} days")
        print()
        
        # VirusTotal Results
        print("=" * 60)
        print("🛡️  VIRUSTOTAL RESULTS")
        print("=" * 60)
        vt = results.get('virustotal', {})
        if vt.get('error'):
            print(f"❌ Error: {vt.get('error')} - {vt.get('message', '')}")
        elif vt.get('success'):
            print(f"Malicious detections: {vt.get('malicious', 0)}")
            print(f"Suspicious detections: {vt.get('suspicious', 0)}")
            print(f"Harmless detections: {vt.get('harmless', 0)}")
            print(f"Reputation score: {vt.get('reputation', 0)}")
            print(f"Country: {vt.get('country', 'Unknown')}")
            print(f"AS Owner: {vt.get('as_owner', 'Unknown')}")
            if vt.get('malicious', 0) > 0:
                print(f"⚠️  Flagged engines: {len(vt.get('flagged_engines', []))}")
        print()
        
        # AbuseIPDB Results
        print("=" * 60)
        print("⚠️  ABUSEIPDB RESULTS")
        print("=" * 60)
        abuse = results.get('abuseipdb', {})
        if abuse.get('error'):
            print(f"❌ Error: {abuse.get('error')} - {abuse.get('message', '')}")
        elif abuse.get('success'):
            score = abuse.get('confidence_score', 0)
            print(f"Abuse confidence score: {score}%")
            print(f"Total reports: {abuse.get('total_reports', 0)}")
            print(f"Number of reporters: {abuse.get('num_distinct_users', 0)}")
            print(f"Country: {abuse.get('country', 'Unknown')}")
            print(f"ISP: {abuse.get('isp', 'Unknown')}")
            print(f"Whitelisted: {abuse.get('is_whitelisted', False)}")
            if abuse.get('categories'):
                print(f"Categories: {', '.join(abuse.get('categories', []))}")
            
            # Risk assessment
            if score == 0:
                print("✅ Status: CLEAN")
            elif score <= 50:
                print("⚠️  Status: SUSPICIOUS")
            else:
                print("🚨 Status: HIGH RISK")
        print()
        
        # Shodan Results
        print("=" * 60)
        print("🔎 SHODAN RESULTS")
        print("=" * 60)
        shodan = results.get('shodan', {})
        if shodan.get('error'):
            print(f"❌ Error: {shodan.get('error')} - {shodan.get('message', '')}")
        elif shodan.get('no_data'):
            print("ℹ️  No Shodan data available for this IP")
        elif shodan.get('success'):
            print(f"Organization: {shodan.get('organization', 'Unknown')}")
            print(f"ISP: {shodan.get('isp', 'Unknown')}")
            print(f"Country: {shodan.get('country', 'Unknown')}")
            print(f"City: {shodan.get('city', 'Unknown')}")
            print(f"Operating System: {shodan.get('os', 'Unknown')}")
            
            ports = shodan.get('ports', [])
            if ports:
                print(f"Open ports: {', '.join(map(str, ports[:10]))}")
                if len(ports) > 10:
                    print(f"  ... and {len(ports) - 10} more")
            
            vulns = shodan.get('vulns', [])
            if vulns:
                print(f"🐛 Vulnerabilities found: {len(vulns)}")
                for vuln in vulns[:5]:
                    print(f"  - {vuln}")
                if len(vulns) > 5:
                    print(f"  ... and {len(vulns) - 5} more")
            else:
                print("✅ No known vulnerabilities")
            
            hostnames = shodan.get('hostnames', [])
            if hostnames:
                print(f"Hostnames: {', '.join(hostnames)}")
        print()
        
        print("=" * 60)
        print("✅ Test completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_threat_intelligence()
