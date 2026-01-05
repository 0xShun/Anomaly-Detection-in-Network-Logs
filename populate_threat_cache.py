#!/usr/bin/env python3
"""
Populate ThreatIntelligenceCache with malicious IPs from Security Anomaly logs.
This script looks up unique IPs from Security Anomaly logs and caches their threat intelligence data.
"""

import os
import django
import sys

# Setup Django
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webplatform.settings')
django.setup()

from dashboard.models import LogEntry, ThreatIntelligenceCache
from dashboard.threat_intel_utils import unified_threat_lookup
from datetime import timedelta
from django.utils import timezone

def populate_cache():
    """Look up unique IPs from Security Anomaly logs."""
    
    print("=" * 80)
    print("THREAT INTELLIGENCE CACHE POPULATOR")
    print("=" * 80)
    
    # Get Security Anomaly IPs from last 24 hours
    last_24h = timezone.now() - timedelta(hours=24)
    
    security_ips = LogEntry.objects.filter(
        classification_name='Security Anomaly',
        timestamp__gte=last_24h
    ).exclude(
        host_ip__isnull=True
    ).exclude(
        host_ip=''
    ).exclude(
        host_ip='unknown'
    ).values_list('host_ip', flat=True).distinct()
    
    total_ips = len(security_ips)
    print(f"\n📊 Found {total_ips} unique IPs in Security Anomaly logs")
    
    if total_ips == 0:
        print("\n❌ No Security Anomaly IPs found. Run filebeat.py first!")
        return
    
    # Check which ones are already cached
    cached_ips = set(ThreatIntelligenceCache.objects.filter(
        ip_address__in=security_ips
    ).values_list('ip_address', flat=True))
    
    uncached_ips = [ip for ip in security_ips if ip not in cached_ips]
    
    print(f"✅ Already cached: {len(cached_ips)}")
    print(f"🔍 Need to lookup: {len(uncached_ips)}")
    
    if len(uncached_ips) == 0:
        print("\n✨ All IPs already cached! Threat map should show data.")
        return
    
    print(f"\n🚀 Looking up {len(uncached_ips)} IPs...")
    print("⚠️  Note: API rate limits apply. This may take a few minutes.\n")
    
    success_count = 0
    error_count = 0
    
    for i, ip in enumerate(uncached_ips, 1):
        print(f"[{i}/{len(uncached_ips)}] Looking up {ip}...", end=" ")
        
        try:
            result = unified_threat_lookup(ip)
            
            if result.get('error'):
                print(f"❌ Error: {result['error']}")
                error_count += 1
            else:
                # Check if it was cached
                if ThreatIntelligenceCache.objects.filter(ip_address=ip).exists():
                    print("✅ Cached")
                    success_count += 1
                else:
                    print("⚠️  Looked up but not cached (no data)")
                    error_count += 1
                    
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            error_count += 1
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully cached: {success_count}")
    print(f"❌ Errors/Skipped: {error_count}")
    print(f"📊 Total in cache: {ThreatIntelligenceCache.objects.count()}")
    print("\n🎉 Done! Refresh the Threat Map to see markers.")
    print("=" * 80)

if __name__ == '__main__':
    populate_cache()
