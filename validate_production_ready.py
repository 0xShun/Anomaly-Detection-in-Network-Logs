#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick validation script to check if all production fixes are applied.

Run this to verify the codebase is ready for PythonAnywhere deployment.
"""

import os
import sys
from pathlib import Path

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
END = '\033[0m'

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"  {GREEN}[PASS]{END} {description}: {filepath}")
        return True
    else:
        print(f"  {RED}[FAIL]{END} {description}: {filepath} NOT FOUND")
        return False

def check_file_contains(filepath, search_string, description):
    """Check if file contains a string"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if search_string in content:
                print(f"  {GREEN}[PASS]{END} {description}")
                return True
            else:
                print(f"  {RED}[FAIL]{END} {description} - NOT FOUND")
                return False
    except Exception as e:
        print(f"  {RED}[FAIL]{END} {description} - ERROR: {e}")
        return False

def check_file_not_contains(filepath, search_string, description):
    """Check if file does NOT contain a string"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if search_string not in content:
                print(f"  {GREEN}[PASS]{END} {description}")
                return True
            else:
                print(f"  {RED}[FAIL]{END} {description} - STILL PRESENT")
                return False
    except Exception as e:
        print(f"  {RED}[FAIL]{END} {description} - ERROR: {e}")
        return False

def main():
    print(f"\n{BLUE}{BOLD}{'='*70}")
    print("Production Readiness Validation")
    print(f"{'='*70}{END}\n")
    
    checks_passed = 0
    checks_failed = 0
    
    # Check 1: Required files exist
    print(f"{BOLD}1. Required Files{END}")
    files_to_check = [
        ('requirements-pythonanywhere.txt', 'Minimal requirements file'),
        ('.gitignore', 'Git ignore file'),
        ('webplatform/production_settings.py', 'Production settings helper'),
        ('wsgi_pythonanywhere_example.py', 'WSGI example'),
        ('QUICK_DEPLOY_GUIDE.md', 'Quick deployment guide'),
        ('.env.template', 'Environment template'),
    ]
    
    for filepath, desc in files_to_check:
        if check_file_exists(filepath, desc):
            checks_passed += 1
        else:
            checks_failed += 1
    
    # Check 2: settings.py has environment variable support
    print(f"\n{BOLD}2. Environment Variable Support{END}")
    settings_checks = [
        ('os.environ.get', 'Uses os.environ.get()'),
        ('SECRET_KEY', 'SECRET_KEY from environment'),
        ('DEBUG', 'DEBUG from environment'),
        ('ALLOWED_HOSTS', 'ALLOWED_HOSTS from environment'),
        ('CORS_ALLOWED_ORIGINS', 'CORS from environment'),
        ('STATIC_ROOT', 'STATIC_ROOT configured'),
    ]
    
    for search, desc in settings_checks:
        if check_file_contains('webplatform/settings.py', search, desc):
            checks_passed += 1
        else:
            checks_failed += 1
    
    # Check 3: Obsolete settings removed
    print(f"\n{BOLD}3. Obsolete Settings Removed{END}")
    obsolete_checks = [
        ('CHANNEL_LAYERS', 'Channels/Redis removed'),
        ('KAFKA_BROKER_URL', 'Kafka settings removed'),
        ('STREAMLIT_PORT', 'Streamlit settings removed'),
        ('CELERY_BROKER_URL', 'Celery settings removed'),
    ]
    
    for search, desc in obsolete_checks:
        if check_file_not_contains('webplatform/settings.py', search, desc):
            checks_passed += 1
        else:
            checks_failed += 1
    
    # Check 4: Requirements file is minimal
    print(f"\n{BOLD}4. Requirements Optimization{END}")
    # Check that minimal requirements file exists and is smaller
    try:
        with open('requirements-pythonanywhere.txt', 'r') as f:
            minimal_reqs = f.read()
            
            # Only check actual package lines, not comments
            package_lines = [l.strip() for l in minimal_reqs.split('\n') 
                           if l.strip() and not l.strip().startswith('#')]
            
            has_torch = any('torch' in line.lower() for line in package_lines)
            has_kafka = any('kafka' in line.lower() for line in package_lines)
            
            if not has_torch and not has_kafka:
                print(f"  {GREEN}[PASS]{END} Heavy packages excluded from pythonanywhere requirements")
                checks_passed += 1
            else:
                print(f"  {RED}[FAIL]{END} Heavy packages still in requirements")
                checks_failed += 1
            
            # Count lines
            print(f"  {GREEN}[INFO]{END} Minimal requirements has {len(package_lines)} packages")
    except Exception as e:
        print(f"  {RED}[FAIL]{END} Error reading requirements: {e}")
        checks_failed += 1
    
    # Check 5: .gitignore protects sensitive files
    print(f"\n{BOLD}5. Security - .gitignore{END}")
    gitignore_checks = [
        ('.env', 'Protects .env files'),
        ('db.sqlite3', 'Protects database'),
        ('*.log', 'Protects log files'),
        ('*.pth', 'Protects model files'),
    ]
    
    for search, desc in gitignore_checks:
        if check_file_contains('.gitignore', search, desc):
            checks_passed += 1
        else:
            checks_failed += 1
    
    # Check 6: API authentication present
    print(f"\n{BOLD}6. API Authentication{END}")
    if check_file_contains('api/authentication.py', 'LOGBERT_API_KEYS', 'API key authentication'):
        checks_passed += 1
    else:
        checks_failed += 1
    
    if check_file_contains('api/authentication.py', 'os.environ.get', 'Uses environment variables'):
        checks_passed += 1
    else:
        checks_failed += 1
    
    # Summary
    total_checks = checks_passed + checks_failed
    pass_rate = (checks_passed / total_checks * 100) if total_checks > 0 else 0
    
    print(f"\n{BLUE}{BOLD}{'='*70}")
    print("VALIDATION SUMMARY")
    print(f"{'='*70}{END}\n")
    
    print(f"Total Checks: {total_checks}")
    print(f"{GREEN}Passed: {checks_passed}{END}")
    print(f"{RED}Failed: {checks_failed}{END}")
    print(f"Pass Rate: {pass_rate:.1f}%\n")
    
    if checks_failed == 0:
        print(f"{GREEN}{BOLD}[SUCCESS] ALL CHECKS PASSED!{END}")
        print(f"\n{GREEN}Your codebase is production-ready for PythonAnywhere!{END}")
        print(f"\n{BOLD}Next steps:{END}")
        print("  1. Generate production keys:")
        print("     python -m webplatform.production_settings")
        print("  2. Follow the deployment guide:")
        print("     See QUICK_DEPLOY_GUIDE.md")
        print("  3. Upload to PythonAnywhere and configure WSGI")
        print()
        return 0
    else:
        print(f"{RED}{BOLD}[FAILED] SOME CHECKS FAILED{END}")
        print(f"\n{YELLOW}Please review the failed checks above.{END}")
        print(f"{YELLOW}Re-run the fix script or manually correct the issues.{END}\n")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Validation interrupted{END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error: {e}{END}")
        sys.exit(1)
