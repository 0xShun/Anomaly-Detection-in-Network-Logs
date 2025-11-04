#!/usr/bin/env python
"""
Pre-deployment validation script for LogBERT Remote Monitoring Platform

Run this script before manual testing to ensure all components are correctly configured.

Usage:
    python validate_setup.py
"""

import os
import sys
import django
import subprocess
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
try:
    init(autoreset=True)
except ImportError:
    # Fallback if colorama not installed
    class Fore:
        GREEN = RED = YELLOW = BLUE = RESET = ""
    class Style:
        BRIGHT = RESET_ALL = ""

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webplatform.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from api.models import Alert, SystemMetric, LogStatistic, RawModelOutput


def print_header(text):
    """Print colored header"""
    print(f"\n{Fore.BLUE}{Style.BRIGHT}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{Style.RESET_ALL}\n")


def print_success(text):
    """Print success message"""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")


def print_error(text):
    """Print error message"""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")


def print_warning(text):
    """Print warning message"""
    print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")


def print_info(text):
    """Print info message"""
    print(f"  {text}")


def check_environment_variables():
    """Check required environment variables"""
    print_header("1. Environment Variables Check")
    
    required_vars = {
        'SECRET_KEY': 'Django secret key',
        'LOGBERT_API_KEYS': 'API keys for authentication'
    }
    
    optional_vars = {
        'DEBUG': 'Debug mode (should be False in production)',
        'ALLOWED_HOSTS': 'Allowed hosts for Django',
        'CORS_ALLOWED_ORIGINS': 'CORS allowed origins'
    }
    
    all_good = True
    
    # Check required variables
    for var, description in required_vars.items():
        value = os.environ.get(var) or getattr(settings, var, None)
        if value:
            # Don't print actual values for security
            masked = value[:4] + '...' if len(str(value)) > 4 else '***'
            print_success(f"{var} is set: {masked}")
        else:
            print_error(f"{var} is NOT set ({description})")
            all_good = False
    
    # Check optional variables
    for var, description in optional_vars.items():
        value = os.environ.get(var) or getattr(settings, var, None)
        if value:
            print_success(f"{var} is set: {value}")
        else:
            print_warning(f"{var} is not set ({description})")
    
    # Check DEBUG setting
    if settings.DEBUG:
        print_warning("DEBUG is True - should be False in production")
    else:
        print_success("DEBUG is False (production mode)")
    
    return all_good


def check_database():
    """Check database connection and migrations"""
    print_header("2. Database Check")
    
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print_success("Database connection successful")
        
        # Check if migrations are applied
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            print_error(f"Unapplied migrations found: {len(plan)} migration(s) pending")
            print_info("Run: python manage.py migrate")
            return False
        else:
            print_success("All migrations applied")
        
        # Check if api app tables exist
        tables = connection.introspection.table_names()
        
        required_tables = ['api_alert', 'api_systemmetric', 'api_logstatistic', 'api_rawmodeloutput']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print_error(f"Missing tables: {', '.join(missing_tables)}")
            print_info("Run: python manage.py makemigrations api")
            print_info("Then: python manage.py migrate")
            return False
        else:
            print_success("All required tables exist")
        
        # Check table row counts
        counts = {
            'Alerts': Alert.objects.count(),
            'Metrics': SystemMetric.objects.count(),
            'Statistics': LogStatistic.objects.count(),
            'Raw Outputs': RawModelOutput.objects.count()
        }
        
        print_info("\nCurrent data counts:")
        for name, count in counts.items():
            print_info(f"  {name}: {count}")
        
        return True
        
    except Exception as e:
        print_error(f"Database error: {str(e)}")
        return False


def check_installed_apps():
    """Check if all required apps are installed"""
    print_header("3. Installed Apps Check")
    
    required_apps = [
        ('api', 'API app'),
        ('rest_framework', 'Django REST Framework'),
        ('corsheaders', 'CORS headers'),
    ]
    
    all_good = True
    
    for app, description in required_apps:
        if app in settings.INSTALLED_APPS:
            print_success(f"{app} is installed ({description})")
        else:
            print_error(f"{app} is NOT installed ({description})")
            all_good = False
    
    return all_good


def check_api_configuration():
    """Check REST Framework configuration"""
    print_header("4. API Configuration Check")
    
    all_good = True
    
    # Check REST_FRAMEWORK settings
    if hasattr(settings, 'REST_FRAMEWORK'):
        print_success("REST_FRAMEWORK settings found")
        
        rf_settings = settings.REST_FRAMEWORK
        
        # Check authentication
        if 'DEFAULT_AUTHENTICATION_CLASSES' in rf_settings:
            auth_classes = rf_settings['DEFAULT_AUTHENTICATION_CLASSES']
            print_info(f"Authentication classes: {len(auth_classes)}")
            for cls in auth_classes:
                print_info(f"  - {cls}")
        else:
            print_warning("No default authentication classes configured")
        
        # Check pagination
        if 'PAGE_SIZE' in rf_settings:
            print_success(f"Pagination configured: {rf_settings['PAGE_SIZE']} items per page")
        else:
            print_warning("No pagination configured")
    else:
        print_error("REST_FRAMEWORK settings not found")
        all_good = False
    
    # Check CORS settings
    if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
        origins = settings.CORS_ALLOWED_ORIGINS
        if origins:
            print_success(f"CORS configured with {len(origins)} allowed origin(s)")
            for origin in origins:
                print_info(f"  - {origin}")
        else:
            print_warning("CORS_ALLOWED_ORIGINS is empty")
    else:
        print_warning("CORS_ALLOWED_ORIGINS not configured")
    
    return all_good


def check_url_configuration():
    """Check URL configuration"""
    print_header("5. URL Configuration Check")
    
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        
        # Check if API URLs are configured
        api_patterns = [p for p in resolver.url_patterns if 'api' in str(p.pattern)]
        
        if api_patterns:
            print_success("API URLs configured")
            for pattern in api_patterns:
                print_info(f"  - {pattern.pattern}")
        else:
            print_error("API URLs not found in main URL configuration")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"URL configuration error: {str(e)}")
        return False


def check_dependencies():
    """Check if required Python packages are installed"""
    print_header("6. Dependencies Check")
    
    # Map of package names to import names
    required_packages = {
        'django': 'django',
        'djangorestframework': 'rest_framework',
        'django-cors-headers': 'corsheaders',
        'requests': 'requests',
    }
    
    all_good = True
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print_success(f"{package_name} is installed")
        except ImportError:
            print_error(f"{package_name} is NOT installed")
            all_good = False
    
    if not all_good:
        print_info("\nInstall missing packages:")
        print_info("  pip install -r requirements.txt")
    
    return all_good


def check_static_files():
    """Check static files configuration"""
    print_header("7. Static Files Check")
    
    if hasattr(settings, 'STATIC_URL'):
        print_success(f"STATIC_URL configured: {settings.STATIC_URL}")
    else:
        print_error("STATIC_URL not configured")
        return False
    
    if hasattr(settings, 'STATIC_ROOT'):
        static_root = Path(settings.STATIC_ROOT)
        print_success(f"STATIC_ROOT configured: {settings.STATIC_ROOT}")
        
        if static_root.exists():
            static_files = list(static_root.rglob('*'))
            print_info(f"Static files collected: {len(static_files)} files")
        else:
            print_warning("STATIC_ROOT directory does not exist")
            print_info("Run: python manage.py collectstatic")
    else:
        print_warning("STATIC_ROOT not configured (needed for production)")
    
    return True


def check_admin_user():
    """Check if admin user exists"""
    print_header("8. Admin User Check")
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        superusers = User.objects.filter(is_superuser=True)
        
        if superusers.exists():
            print_success(f"Admin user(s) exist: {superusers.count()} superuser(s)")
            for user in superusers:
                print_info(f"  - {user.username}")
        else:
            print_warning("No admin user found")
            print_info("Create one with: python manage.py createsuperuser")
        
        return True
    except Exception as e:
        print_error(f"Check failed with error: {e}")
        return False


def check_api_key_format():
    """Check API key format"""
    print_header("9. API Key Validation")
    
    api_keys_str = os.environ.get('LOGBERT_API_KEYS', '')
    
    if not api_keys_str:
        print_error("LOGBERT_API_KEYS not set in environment")
        print_info("Generate keys with: python -c 'import secrets; print(secrets.token_urlsafe(32))'")
        return False
    
    api_keys = [k.strip() for k in api_keys_str.split(',') if k.strip()]
    
    if not api_keys:
        print_error("LOGBERT_API_KEYS is empty")
        return False
    
    print_success(f"Found {len(api_keys)} API key(s)")
    
    for i, key in enumerate(api_keys, 1):
        if len(key) < 20:
            print_warning(f"Key {i} is short ({len(key)} chars) - consider longer keys")
        else:
            print_info(f"Key {i}: {key[:4]}...{key[-4:]} ({len(key)} chars)")
    
    return True


def run_basic_tests():
    """Run basic Django tests"""
    print_header("10. Running Basic Tests")
    
    try:
        print_info("Running Django test suite...")
        # Run tests silently
        result = call_command('test', 'api', '--verbosity=1', '--failfast')
        print_success("All tests passed!")
        return True
    except Exception as e:
        print_error(f"Tests failed: {str(e)}")
        print_info("Run manually: python manage.py test api --verbosity=2")
        return False


def check_local_pusher_script():
    """Check if local pusher script exists and is configured"""
    print_header("11. Local Pusher Script Check")
    
    pusher_path = Path(__file__).parent.parent / 'local_network_pusher.py'
    
    if pusher_path.exists():
        print_success(f"local_network_pusher.py found: {pusher_path}")
        
        # Check if it's executable
        if os.access(pusher_path, os.X_OK):
            print_success("Script is executable")
        else:
            print_warning("Script is not executable")
            print_info(f"Make it executable: chmod +x {pusher_path}")
        
        # Check required environment variables for pusher
        pusher_vars = {
            'LOGBERT_API_KEY': os.environ.get('LOGBERT_API_KEY'),
            'LOGBERT_REMOTE_URL': os.environ.get('LOGBERT_REMOTE_URL')
        }
        
        print_info("\nPusher environment variables:")
        for var, value in pusher_vars.items():
            if value:
                masked = value[:8] + '...' if len(value) > 8 else '***'
                print_success(f"  {var}: {masked}")
            else:
                print_warning(f"  {var}: not set (needed for pusher script)")
        
        return True
    else:
        print_error(f"local_network_pusher.py not found at {pusher_path}")
        return False


def main():
    """Run all validation checks"""
    print(f"\n{Fore.BLUE}{Style.BRIGHT}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     LogBERT Remote Monitoring - Setup Validation          ║")
    print("╔════════════════════════════════════════════════════════════╗")
    print(Style.RESET_ALL)
    
    checks = [
        ("Environment Variables", check_environment_variables),
        ("Database", check_database),
        ("Installed Apps", check_installed_apps),
        ("API Configuration", check_api_configuration),
        ("URL Configuration", check_url_configuration),
        ("Dependencies", check_dependencies),
        ("Static Files", check_static_files),
        ("Admin User", check_admin_user),
        ("API Keys", check_api_key_format),
        ("Local Pusher Script", check_local_pusher_script),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Check failed with error: {str(e)}")
            results.append((name, False))
    
    # Optional: Run tests (can be slow)
    print_info("\nWould you like to run the test suite? (y/n)")
    try:
        response = input().strip().lower()
        if response == 'y':
            test_result = run_basic_tests()
            results.append(("Test Suite", test_result))
    except:
        print_info("Skipping test suite...")
    
    # Summary
    print_header("Validation Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Fore.GREEN}✓ PASS" if result else f"{Fore.RED}✗ FAIL"
        print(f"{status}{Style.RESET_ALL} - {name}")
    
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"Results: {passed}/{total} checks passed")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    if passed == total:
        print(f"{Fore.GREEN}{Style.BRIGHT}")
        print("✓ All checks passed! System is ready for manual testing.")
        print(Style.RESET_ALL)
        print("\nNext steps:")
        print("  1. Start dev server: python manage.py runserver")
        print("  2. Access admin: http://localhost:8000/admin")
        print("  3. Test API: python test_api.py")
        print("  4. Test pusher: python ../local_network_pusher.py --school-id test --output-dir ../output")
        return 0
    else:
        print(f"{Fore.RED}{Style.BRIGHT}")
        print(f"✗ {total - passed} check(s) failed. Please fix issues before deployment.")
        print(Style.RESET_ALL)
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)
