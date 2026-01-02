"""
Threat Intelligence Utilities
Handles API queries, rate limiting, and caching for threat intelligence services:
- VirusTotal
- AbuseIPDB  
- Shodan
"""
import os
import requests
import time
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from .models import ThreatIntelligenceCache


# Rate limiting configuration
RATE_LIMITS = {
    'virustotal': {'requests_per_minute': 4, 'requests_per_day': 500},
    'abuseipdb': {'requests_per_day': 1000},
    'shodan': {'requests_per_second': 1, 'requests_per_month': 100}
}

# Cache keys for rate limiting
RATE_LIMIT_CACHE_KEYS = {
    'vt_minute': 'threat_intel_vt_minute_count',
    'vt_day': 'threat_intel_vt_day_count',
    'abuseipdb_day': 'threat_intel_abuseipdb_day_count',
    'shodan_second': 'threat_intel_shodan_second_count',
    'shodan_month': 'threat_intel_shodan_month_count',
}


def check_rate_limit(service):
    """
    Check if we can make a request to the service without hitting rate limits.
    Returns (can_request: bool, wait_time: int, message: str)
    """
    if service == 'virustotal':
        # Check minute limit
        minute_count = cache.get(RATE_LIMIT_CACHE_KEYS['vt_minute'], 0)
        if minute_count >= RATE_LIMITS['virustotal']['requests_per_minute']:
            return False, 60, "VirusTotal rate limit: 4 requests per minute exceeded. Please wait."
        
        # Check day limit
        day_count = cache.get(RATE_LIMIT_CACHE_KEYS['vt_day'], 0)
        if day_count >= RATE_LIMITS['virustotal']['requests_per_day']:
            return False, 86400, "VirusTotal daily limit reached (500 requests). Try again tomorrow."
    
    elif service == 'abuseipdb':
        day_count = cache.get(RATE_LIMIT_CACHE_KEYS['abuseipdb_day'], 0)
        if day_count >= RATE_LIMITS['abuseipdb']['requests_per_day']:
            return False, 86400, "AbuseIPDB daily limit reached (1000 requests). Try again tomorrow."
    
    elif service == 'shodan':
        # Check second limit
        second_count = cache.get(RATE_LIMIT_CACHE_KEYS['shodan_second'], 0)
        if second_count >= RATE_LIMITS['shodan']['requests_per_second']:
            return False, 2, "Shodan rate limit: 1 request per second. Please wait."
        
        # Check month limit
        month_count = cache.get(RATE_LIMIT_CACHE_KEYS['shodan_month'], 0)
        if month_count >= RATE_LIMITS['shodan']['requests_per_month']:
            return False, 2592000, "Shodan monthly limit reached (100 requests). Try again next month."
    
    return True, 0, ""


def increment_rate_limit(service):
    """Increment the rate limit counter for a service"""
    if service == 'virustotal':
        # Increment minute counter (expires in 60 seconds)
        minute_count = cache.get(RATE_LIMIT_CACHE_KEYS['vt_minute'], 0)
        cache.set(RATE_LIMIT_CACHE_KEYS['vt_minute'], minute_count + 1, 60)
        
        # Increment day counter (expires in 24 hours)
        day_count = cache.get(RATE_LIMIT_CACHE_KEYS['vt_day'], 0)
        cache.set(RATE_LIMIT_CACHE_KEYS['vt_day'], day_count + 1, 86400)
    
    elif service == 'abuseipdb':
        day_count = cache.get(RATE_LIMIT_CACHE_KEYS['abuseipdb_day'], 0)
        cache.set(RATE_LIMIT_CACHE_KEYS['abuseipdb_day'], day_count + 1, 86400)
    
    elif service == 'shodan':
        # Increment second counter (expires in 2 seconds for safety)
        second_count = cache.get(RATE_LIMIT_CACHE_KEYS['shodan_second'], 0)
        cache.set(RATE_LIMIT_CACHE_KEYS['shodan_second'], second_count + 1, 2)
        
        # Increment month counter (expires in 30 days)
        month_count = cache.get(RATE_LIMIT_CACHE_KEYS['shodan_month'], 0)
        cache.set(RATE_LIMIT_CACHE_KEYS['shodan_month'], month_count + 1, 2592000)


def get_cached_threat_intel(ip_address, max_age_days=7):
    """
    Get cached threat intelligence data for an IP address.
    Returns (cache_object, is_expired) tuple.
    """
    try:
        cache_obj = ThreatIntelligenceCache.objects.get(ip_address=ip_address)
        is_expired = cache_obj.is_expired(days=max_age_days)
        return cache_obj, is_expired
    except ThreatIntelligenceCache.DoesNotExist:
        return None, True


def query_virustotal(ip_address):
    """
    Query VirusTotal API for IP address information.
    Returns dict with results or error.
    """
    api_key = os.environ.get('VIRUSTOTAL_API_KEY')
    if not api_key:
        return {'error': 'VirusTotal API key not configured'}
    
    # Check rate limit
    can_request, wait_time, message = check_rate_limit('virustotal')
    if not can_request:
        return {'error': 'Rate limit exceeded', 'message': message, 'wait_time': wait_time}
    
    try:
        url = f'https://www.virustotal.com/api/v3/ip_addresses/{ip_address}'
        headers = {'x-apikey': api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        increment_rate_limit('virustotal')
        
        if response.status_code == 404:
            return {
                'success': True,
                'clean': True,
                'malicious': 0,
                'suspicious': 0,
                'harmless': 0,
                'undetected': 0,
                'reputation': 0,
                'country': 'Unknown',
                'asn': 'Unknown',
                'as_owner': 'Unknown',
                'last_analysis_date': 'Not analyzed',
                'flagged_engines': []
            }
        
        if response.status_code != 200:
            return {'error': f'VirusTotal API error: {response.status_code}'}
        
        data = response.json()
        attrs = data.get('data', {}).get('attributes', {})
        stats = attrs.get('last_analysis_stats', {})
        
        # Get flagged engines
        results = attrs.get('last_analysis_results', {})
        flagged_engines = []
        for engine, result in results.items():
            if result.get('category') in ['malicious', 'suspicious']:
                flagged_engines.append({
                    'engine': engine,
                    'category': result.get('category'),
                    'result': result.get('result', 'malicious')
                })
        
        # Format last analysis date
        last_analysis = attrs.get('last_analysis_date')
        if last_analysis:
            last_analysis = datetime.fromtimestamp(last_analysis).strftime('%Y-%m-%d %H:%M:%S UTC')
        else:
            last_analysis = 'Unknown'
        
        return {
            'success': True,
            'clean': stats.get('malicious', 0) == 0 and stats.get('suspicious', 0) == 0,
            'malicious': stats.get('malicious', 0),
            'suspicious': stats.get('suspicious', 0),
            'harmless': stats.get('harmless', 0),
            'undetected': stats.get('undetected', 0),
            'reputation': attrs.get('reputation', 0),
            'country': attrs.get('country', 'Unknown'),
            'asn': str(attrs.get('asn', 'Unknown')),
            'as_owner': attrs.get('as_owner', 'Unknown'),
            'last_analysis_date': last_analysis,
            'flagged_engines': flagged_engines[:10]
        }
        
    except requests.RequestException as e:
        return {'error': f'VirusTotal request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'VirusTotal error: {str(e)}'}


def query_abuseipdb(ip_address):
    """
    Query AbuseIPDB API for IP reputation information.
    Returns dict with results or error.
    """
    api_key = os.environ.get('ABUSEIPDB_API_KEY')
    if not api_key:
        return {'error': 'AbuseIPDB API key not configured'}
    
    # Check rate limit
    can_request, wait_time, message = check_rate_limit('abuseipdb')
    if not can_request:
        return {'error': 'Rate limit exceeded', 'message': message, 'wait_time': wait_time}
    
    try:
        url = 'https://api.abuseipdb.com/api/v2/check'
        headers = {
            'Key': api_key,
            'Accept': 'application/json'
        }
        params = {
            'ipAddress': ip_address,
            'maxAgeInDays': 90,
            'verbose': True
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        increment_rate_limit('abuseipdb')
        
        if response.status_code != 200:
            return {'error': f'AbuseIPDB API error: {response.status_code}'}
        
        data = response.json().get('data', {})
        
        # Map category IDs to names
        category_map = {
            3: 'Fraud Orders', 4: 'DDoS Attack', 5: 'FTP Brute-Force',
            6: 'Ping of Death', 7: 'Phishing', 8: 'Fraud VoIP',
            9: 'Open Proxy', 10: 'Web Spam', 11: 'Email Spam',
            12: 'Blog Spam', 13: 'VPN IP', 14: 'Port Scan',
            15: 'Hacking', 16: 'SQL Injection', 17: 'Spoofing',
            18: 'Brute-Force', 19: 'Bad Web Bot', 20: 'Exploited Host',
            21: 'Web App Attack', 22: 'SSH', 23: 'IoT Targeted'
        }
        
        # Get categories
        reports = data.get('reports', [])
        categories_set = set()
        for report in reports:
            for cat_id in report.get('categories', []):
                if cat_id in category_map:
                    categories_set.add(category_map[cat_id])
        
        categories = list(categories_set)[:5]  # Top 5 categories
        
        # Get last reported date
        last_reported = data.get('lastReportedAt', '')
        if last_reported:
            try:
                last_reported = datetime.fromisoformat(last_reported.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S UTC')
            except:
                pass
        
        return {
            'success': True,
            'clean': data.get('abuseConfidenceScore', 0) == 0,
            'confidence_score': data.get('abuseConfidenceScore', 0),
            'total_reports': data.get('totalReports', 0),
            'num_distinct_users': data.get('numDistinctUsers', 0),
            'country': data.get('countryCode', 'Unknown'),
            'isp': data.get('isp', 'Unknown'),
            'usage_type': data.get('usageType', 'Unknown'),
            'is_whitelisted': data.get('isWhitelisted', False),
            'categories': categories,
            'last_reported_at': last_reported
        }
        
    except requests.RequestException as e:
        return {'error': f'AbuseIPDB request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'AbuseIPDB error: {str(e)}'}


def query_shodan(ip_address):
    """
    Query Shodan API for IP information.
    Returns dict with results or error.
    """
    api_key = os.environ.get('SHODAN_API_KEY')
    if not api_key:
        return {'error': 'Shodan API key not configured'}
    
    # Check rate limit
    can_request, wait_time, message = check_rate_limit('shodan')
    if not can_request:
        return {'error': 'Rate limit exceeded', 'message': message, 'wait_time': wait_time}
    
    try:
        url = f'https://api.shodan.io/shodan/host/{ip_address}'
        params = {'key': api_key}
        
        response = requests.get(url, params=params, timeout=10)
        increment_rate_limit('shodan')
        
        if response.status_code == 404:
            return {
                'success': True,
                'no_data': True,
                'message': 'No Shodan data available for this IP'
            }
        
        if response.status_code != 200:
            return {'error': f'Shodan API error: {response.status_code}'}
        
        data = response.json()
        
        # Extract ports and services
        ports = data.get('ports', [])
        
        # Extract vulnerabilities (CVEs)
        vulns = data.get('vulns', [])
        
        # Extract hostnames
        hostnames = data.get('hostnames', [])
        
        # Extract domains
        domains = data.get('domains', [])
        
        # Extract CPEs (Common Platform Enumeration)
        cpes = []
        for item in data.get('data', []):
            item_cpes = item.get('cpe', [])
            if item_cpes:
                cpes.extend(item_cpes)
        cpes = list(set(cpes))[:10]  # Unique CPEs, max 10
        
        # Get tags
        tags = data.get('tags', [])
        
        # Get last update
        last_update = data.get('last_update', '')
        
        return {
            'success': True,
            'no_data': False,
            'hostnames': hostnames[:5],
            'domains': domains[:5],
            'ports': ports[:20],
            'vulns': vulns[:10],
            'cpes': cpes,
            'organization': data.get('org', 'Unknown'),
            'os': data.get('os', 'Unknown'),
            'country': data.get('country_name', 'Unknown'),
            'city': data.get('city', 'Unknown'),
            'isp': data.get('isp', 'Unknown'),
            'tags': tags[:5],
            'last_update': last_update
        }
        
    except requests.RequestException as e:
        return {'error': f'Shodan request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Shodan error: {str(e)}'}


def unified_threat_lookup(ip_address):
    """
    Perform unified threat intelligence lookup across all services.
    Returns combined results from VirusTotal, AbuseIPDB, and Shodan.
    Uses caching to avoid hitting rate limits.
    """
    # Check cache first
    cache_obj, is_expired = get_cached_threat_intel(ip_address)
    
    if cache_obj and not is_expired:
        # Return cached data
        return {
            'success': True,
            'cached': True,
            'cache_age': (timezone.now() - cache_obj.updated_at).days,
            'ip_address': ip_address,
            'virustotal': {
                'success': cache_obj.vt_queried_at is not None,
                'malicious': cache_obj.vt_malicious,
                'suspicious': cache_obj.vt_suspicious,
                'harmless': cache_obj.vt_harmless,
                'undetected': cache_obj.vt_undetected,
                'reputation': cache_obj.vt_reputation,
                'country': cache_obj.vt_country,
                'asn': cache_obj.vt_asn,
                'as_owner': cache_obj.vt_as_owner,
                'last_analysis_date': cache_obj.vt_last_analysis_date,
                'flagged_engines': cache_obj.vt_flagged_engines or []
            },
            'abuseipdb': {
                'success': cache_obj.abuseipdb_queried_at is not None,
                'confidence_score': cache_obj.abuseipdb_confidence_score,
                'total_reports': cache_obj.abuseipdb_total_reports,
                'num_distinct_users': cache_obj.abuseipdb_num_distinct_users,
                'country': cache_obj.abuseipdb_country,
                'isp': cache_obj.abuseipdb_isp,
                'usage_type': cache_obj.abuseipdb_usage_type,
                'is_whitelisted': cache_obj.abuseipdb_is_whitelisted,
                'categories': cache_obj.abuseipdb_categories or [],
                'last_reported_at': cache_obj.abuseipdb_last_reported_at
            },
            'shodan': {
                'success': cache_obj.shodan_queried_at is not None,
                'hostnames': cache_obj.shodan_hostnames or [],
                'domains': cache_obj.shodan_domains or [],
                'ports': cache_obj.shodan_ports or [],
                'vulns': cache_obj.shodan_vulns or [],
                'cpes': cache_obj.shodan_cpes or [],
                'organization': cache_obj.shodan_organization,
                'os': cache_obj.shodan_os,
                'country': cache_obj.shodan_country,
                'city': cache_obj.shodan_city,
                'isp': cache_obj.shodan_isp,
                'tags': cache_obj.shodan_tags or [],
                'last_update': cache_obj.shodan_last_update
            }
        }
    
    # Cache miss or expired - query APIs
    results = {
        'success': True,
        'cached': False,
        'ip_address': ip_address,
        'virustotal': {},
        'abuseipdb': {},
        'shodan': {}
    }
    
    # Query each service
    vt_result = query_virustotal(ip_address)
    abuseipdb_result = query_abuseipdb(ip_address)
    shodan_result = query_shodan(ip_address)
    
    results['virustotal'] = vt_result
    results['abuseipdb'] = abuseipdb_result
    results['shodan'] = shodan_result
    
    # Update or create cache
    if not cache_obj:
        cache_obj = ThreatIntelligenceCache(ip_address=ip_address)
    
    # Store VirusTotal data
    if vt_result.get('success'):
        cache_obj.vt_malicious = vt_result.get('malicious')
        cache_obj.vt_suspicious = vt_result.get('suspicious')
        cache_obj.vt_harmless = vt_result.get('harmless')
        cache_obj.vt_undetected = vt_result.get('undetected')
        cache_obj.vt_reputation = vt_result.get('reputation')
        cache_obj.vt_country = vt_result.get('country', '')
        cache_obj.vt_asn = vt_result.get('asn', '')
        cache_obj.vt_as_owner = vt_result.get('as_owner', '')
        cache_obj.vt_last_analysis_date = vt_result.get('last_analysis_date', '')
        cache_obj.vt_flagged_engines = vt_result.get('flagged_engines', [])
        cache_obj.vt_queried_at = timezone.now()
    
    # Store AbuseIPDB data
    if abuseipdb_result.get('success'):
        cache_obj.abuseipdb_confidence_score = abuseipdb_result.get('confidence_score')
        cache_obj.abuseipdb_total_reports = abuseipdb_result.get('total_reports')
        cache_obj.abuseipdb_num_distinct_users = abuseipdb_result.get('num_distinct_users')
        cache_obj.abuseipdb_country = abuseipdb_result.get('country', '')
        cache_obj.abuseipdb_isp = abuseipdb_result.get('isp', '')
        cache_obj.abuseipdb_usage_type = abuseipdb_result.get('usage_type', '')
        cache_obj.abuseipdb_categories = abuseipdb_result.get('categories', [])
        cache_obj.abuseipdb_is_whitelisted = abuseipdb_result.get('is_whitelisted', False)
        cache_obj.abuseipdb_last_reported_at = abuseipdb_result.get('last_reported_at', '')
        cache_obj.abuseipdb_queried_at = timezone.now()
    
    # Store Shodan data
    if shodan_result.get('success') and not shodan_result.get('no_data'):
        cache_obj.shodan_hostnames = shodan_result.get('hostnames', [])
        cache_obj.shodan_domains = shodan_result.get('domains', [])
        cache_obj.shodan_ports = shodan_result.get('ports', [])
        cache_obj.shodan_vulns = shodan_result.get('vulns', [])
        cache_obj.shodan_cpes = shodan_result.get('cpes', [])
        cache_obj.shodan_organization = shodan_result.get('organization', '')
        cache_obj.shodan_os = shodan_result.get('os', '')
        cache_obj.shodan_country = shodan_result.get('country', '')
        cache_obj.shodan_city = shodan_result.get('city', '')
        cache_obj.shodan_isp = shodan_result.get('isp', '')
        cache_obj.shodan_tags = shodan_result.get('tags', [])
        cache_obj.shodan_last_update = shodan_result.get('last_update', '')
        cache_obj.shodan_queried_at = timezone.now()
    
    cache_obj.save()
    
    return results
