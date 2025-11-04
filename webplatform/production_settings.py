"""
Production settings helper for PythonAnywhere deployment.

This module helps configure environment variables for production.
Import and call configure_production() from your WSGI file.
"""

import os
import sys


def configure_production(wsgi_environ=None):
    """
    Configure production environment variables.
    
    Args:
        wsgi_environ: Dictionary of environment variables (from WSGI file)
    
    Returns:
        dict: Configuration summary
    
    Usage in WSGI file:
        from webplatform.production_settings import configure_production
        
        # Set environment variables
        configure_production({
            'SECRET_KEY': 'your-secret-key-here',
            'DEBUG': 'False',
            'ALLOWED_HOSTS': 'yourusername.pythonanywhere.com',
            'LOGBERT_API_KEYS': 'key1,key2,key3',
            'CORS_ALLOWED_ORIGINS': 'https://yourschool.edu,http://192.168.1.100',
        })
    """
    
    if wsgi_environ:
        # Update os.environ with WSGI environment variables
        for key, value in wsgi_environ.items():
            os.environ[key] = str(value)
    
    # Validate critical settings
    warnings = []
    errors = []
    
    # Check SECRET_KEY
    secret_key = os.environ.get('SECRET_KEY', '')
    if not secret_key:
        errors.append('SECRET_KEY not set in environment!')
    elif secret_key.startswith('django-insecure'):
        warnings.append('SECRET_KEY appears to be the default insecure key!')
    
    # Check API keys
    api_keys = os.environ.get('LOGBERT_API_KEYS', '')
    if not api_keys:
        errors.append('LOGBERT_API_KEYS not set in environment!')
    else:
        keys = [k.strip() for k in api_keys.split(',') if k.strip()]
        if len(keys) == 0:
            errors.append('LOGBERT_API_KEYS is empty!')
        elif any(len(k) < 20 for k in keys):
            warnings.append('Some API keys are too short (< 20 chars)')
    
    # Check DEBUG setting
    debug = os.environ.get('DEBUG', 'False')
    if debug == 'True':
        warnings.append('DEBUG is True in production - this is insecure!')
    
    # Check ALLOWED_HOSTS
    allowed_hosts = os.environ.get('ALLOWED_HOSTS', '')
    if not allowed_hosts:
        warnings.append('ALLOWED_HOSTS not set - using default')
    
    # Print configuration status
    print("="*70)
    print("LogBERT Production Configuration")
    print("="*70)
    
    config = {
        'SECRET_KEY': '***' + secret_key[-4:] if secret_key else 'NOT SET',
        'DEBUG': debug,
        'ALLOWED_HOSTS': allowed_hosts if allowed_hosts else 'localhost,127.0.0.1',
        'API_KEYS_COUNT': len([k for k in api_keys.split(',') if k.strip()]),
        'CORS_ORIGINS': os.environ.get('CORS_ALLOWED_ORIGINS', 'default'),
    }
    
    for key, value in config.items():
        print(f"{key}: {value}")
    
    if errors:
        print("\n❌ ERRORS:")
        for error in errors:
            print(f"  - {error}")
        print("\n⚠️  Application may not work correctly!")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("\n✅ Configuration looks good!")
    
    print("="*70)
    
    return {
        'config': config,
        'errors': errors,
        'warnings': warnings,
    }


def generate_secret_key():
    """
    Generate a new Django secret key.
    
    Returns:
        str: A secure random secret key
    """
    import secrets
    return secrets.token_urlsafe(50)


def generate_api_key():
    """
    Generate a new API key for authentication.
    
    Returns:
        str: A secure random API key
    """
    import secrets
    return secrets.token_urlsafe(32)


if __name__ == '__main__':
    """
    Run this script to generate new keys for production.
    
    Usage:
        python -m webplatform.production_settings
    """
    print("\n" + "="*70)
    print("Generate Production Keys")
    print("="*70 + "\n")
    
    print("SECRET_KEY (use for Django SECRET_KEY):")
    print(f"  {generate_secret_key()}\n")
    
    print("API Keys (use for LOGBERT_API_KEYS, comma-separated):")
    for i in range(3):
        print(f"  {generate_api_key()}")
    
    print("\n" + "="*70)
    print("Add these to your PythonAnywhere WSGI file:")
    print("="*70)
    print("""
# In /var/www/yourusername_pythonanywhere_com_wsgi.py

import os
import sys

# Add project to path
path = '/home/yourusername/logbert/webplatform'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['SECRET_KEY'] = 'paste-secret-key-here'
os.environ['DEBUG'] = 'False'
os.environ['ALLOWED_HOSTS'] = 'yourusername.pythonanywhere.com'
os.environ['LOGBERT_API_KEYS'] = 'key1,key2,key3'
os.environ['CORS_ALLOWED_ORIGINS'] = 'https://yourschool.edu,http://192.168.1.100'

# Import Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webplatform.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
""")
    print("="*70 + "\n")
