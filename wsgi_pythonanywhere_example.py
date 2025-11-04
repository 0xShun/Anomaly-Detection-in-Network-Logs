"""
WSGI configuration example for PythonAnywhere deployment.

Copy this content to your PythonAnywhere WSGI file at:
/var/www/yourusername_pythonanywhere_com_wsgi.py

Instructions:
1. Replace 'yourusername' with your PythonAnywhere username
2. Generate new SECRET_KEY and API keys (see below)
3. Update ALLOWED_HOSTS with your actual domain
4. Add your school network IPs/domains to CORS_ALLOWED_ORIGINS
"""

import os
import sys

# ============================================================================
# STEP 1: Add your project directory to the sys.path
# ============================================================================
# Replace 'yourusername' with your actual PythonAnywhere username
path = '/home/yourusername/logbert/webplatform'
if path not in sys.path:
    sys.path.insert(0, path)

# ============================================================================
# STEP 2: Set environment variables for production
# ============================================================================

# Generate these keys by running:
#   python -m webplatform.production_settings
# Or:
#   python -c 'import secrets; print(secrets.token_urlsafe(50))'  # SECRET_KEY
#   python -c 'import secrets; print(secrets.token_urlsafe(32))'  # API_KEY

# CRITICAL: Change these values!
os.environ['SECRET_KEY'] = 'YOUR-SECRET-KEY-HERE-CHANGE-THIS'

# Security settings
os.environ['DEBUG'] = 'False'  # MUST be False in production!

# Your PythonAnywhere domain (change 'yourusername')
os.environ['ALLOWED_HOSTS'] = 'yourusername.pythonanywhere.com'

# API keys for authentication (comma-separated, generate 2-3 keys)
os.environ['LOGBERT_API_KEYS'] = 'your-api-key-1,your-api-key-2,your-api-key-3'

# CORS - Allow your school network to push data
# Add your school's network IPs or domains (comma-separated)
os.environ['CORS_ALLOWED_ORIGINS'] = 'https://yourschool.edu,http://192.168.1.100:8000'

# ============================================================================
# STEP 3: Initialize Django application
# ============================================================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webplatform.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# ============================================================================
# Optional: Print configuration status (helpful for debugging)
# ============================================================================
# Uncomment the following lines to see configuration on reload:
# from webplatform.production_settings import configure_production
# configure_production()

print("✅ LogBERT WSGI application loaded successfully")
print(f"   Domain: {os.environ.get('ALLOWED_HOSTS', 'NOT SET')}")
print(f"   Debug: {os.environ.get('DEBUG', 'NOT SET')}")
print(f"   API Keys configured: {len([k for k in os.environ.get('LOGBERT_API_KEYS', '').split(',') if k.strip()])}")
