# PythonAnywhere Deployment Readiness Checklist

## ⚠️ CRITICAL ISSUES TO FIX BEFORE DEPLOYMENT

### 1. Security Settings (HIGH PRIORITY)

#### ❌ **settings.py has hardcoded insecure values**

**Current issues in `/webplatform/webplatform/settings.py`:**

```python
# Line 23 - INSECURE SECRET KEY
SECRET_KEY = 'django-insecure-z+m_ka=$tk74wq_r$a_g&n+at8l7e#t%qne430tr@oh0jixwv@'
# ❌ This is the default Django secret key - MUST be changed!

# Line 26 - DEBUG MODE ON
DEBUG = True
# ❌ Must be False in production - exposes sensitive information!

# Line 28 - EMPTY ALLOWED_HOSTS
ALLOWED_HOSTS = []
# ❌ Must include your PythonAnywhere domain!
```

**MUST FIX:**
- [ ] Change SECRET_KEY to use environment variable
- [ ] Set DEBUG = False (or use environment variable)
- [ ] Add ALLOWED_HOSTS with PythonAnywhere domain
- [ ] Add STATIC_ROOT for collectstatic

### 2. Missing Environment Variable Support

**Current issue:** `settings.py` does NOT read from environment variables!

The `.env.template` exists but `settings.py` doesn't use `os.environ.get()` anywhere.

**MUST ADD:**
```python
import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# API Keys for authentication
LOGBERT_API_KEYS = os.environ.get('LOGBERT_API_KEYS', '').split(',')

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
```

### 3. Missing Static Files Configuration

**Current issue:** No STATIC_ROOT defined!

**MUST ADD to settings.py:**
```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

This is required for `python manage.py collectstatic` to work on PythonAnywhere.

### 4. Unnecessary Dependencies for PythonAnywhere

**Issues in `requirements.txt`:**

These are NOT needed for PythonAnywhere deployment and will cause issues:

```txt
❌ channels==4.3.1              # Requires Redis (not available on free tier)
❌ kafka-python==2.2.15         # Not needed for remote monitoring
❌ torch==2.8.0                 # HUGE (800MB+) - inference done locally
❌ transformers==4.55.0         # Not needed - models run locally
❌ fastapi==0.115.4             # Using Django, not FastAPI
❌ uvicorn==0.30.6              # FastAPI server - not needed
```

**Recommended minimal requirements.txt for PythonAnywhere:**
```txt
Django==5.2.5
djangorestframework==3.14.0
django-cors-headers==4.3.1
requests==2.32.4
psutil==7.0.0
sqlparse==0.5.3
crispy-bootstrap5==2025.6
django-crispy-forms==2.4
matplotlib==3.10.5
seaborn==0.13.2
plotly==5.24.1
```

### 5. Obsolete Configuration in settings.py

**Remove these sections before deployment:**

```python
# Lines 180-187 - Channels/Redis (not used in API-only deployment)
ASGI_APPLICATION = 'webplatform.asgi.application'
CHANNEL_LAYERS = {...}

# Lines 189-192 - Kafka (not used in remote monitoring)
KAFKA_BROKER_URL = 'localhost:9092'
KAFKA_TOPIC_LOGS = 'logs'
KAFKA_TOPIC_ANOMALIES = 'anomalies'

# Lines 194-196 - Streamlit (removed)
STREAMLIT_PORT = 8501
STREAMLIT_HOST = 'localhost'

# Lines 198-203 - Celery/Redis (not needed)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
...
```

## ✅ WHAT'S ALREADY GOOD

### Positive Points:

1. ✅ **API app structure is correct**
   - Models, views, serializers, authentication all present
   - API endpoints properly configured

2. ✅ **SQLite database**
   - Perfect for PythonAnywhere
   - No external database needed

3. ✅ **API authentication implemented**
   - Uses environment variables (good!)
   - `api/authentication.py` properly checks `LOGBERT_API_KEYS`

4. ✅ **CORS configured**
   - `corsheaders` in INSTALLED_APPS
   - `CORS_ALLOWED_ORIGINS` defined

5. ✅ **REST Framework configured**
   - Good default settings
   - Pagination enabled
   - JSON renderer configured

6. ✅ **Comprehensive testing suite**
   - Unit tests in `api/tests.py`
   - Integration tests in `comprehensive_api_test.py`
   - Validation script in `validate_setup.py`

7. ✅ **Documentation**
   - DEPLOYMENT.md with PythonAnywhere instructions
   - TESTING_GUIDE.md
   - TESTING_SUMMARY.md

## 🔧 REQUIRED CHANGES BEFORE UPLOAD

### Step 1: Update settings.py

**File: `/webplatform/webplatform/settings.py`**

Add at the top (after imports):
```python
import os

# Environment variable support
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-z+m_ka=$tk74wq_r$a_g&n+at8l7e#t%qne430tr@oh0jixwv@')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]
```

Add static files configuration:
```python
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # ADD THIS LINE
STATICFILES_DIRS = [BASE_DIR / "static"]
```

Remove obsolete sections:
- ASGI_APPLICATION and CHANNEL_LAYERS
- KAFKA_* settings
- STREAMLIT_* settings  
- CELERY_* settings

Update CORS:
```python
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:8081,http://127.0.0.1:8081'
    ).split(',') if o.strip()
]
```

### Step 2: Create Minimal requirements.txt

**File: `/webplatform/requirements-pythonanywhere.txt`**

Create a separate, minimal requirements file for PythonAnywhere:
```txt
Django==5.2.5
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-crispy-forms==2.4
crispy-bootstrap5==2025.6
requests==2.32.4
psutil==7.0.0
sqlparse==0.5.3
matplotlib==3.10.5
seaborn==0.13.2
plotly==5.24.1
numpy==2.3.2
pandas==2.3.1
python-dateutil==2.9.0.post0
```

### Step 3: Create .gitignore

**File: `/webplatform/.gitignore`**

```gitignore
# Environment files
.env
*.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Django
*.log
db.sqlite3
db.sqlite3-journal
staticfiles/
media/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

### Step 4: Create Production Settings Helper

**File: `/webplatform/webplatform/production_settings.py`**

```python
"""
Production settings for PythonAnywhere deployment.
Import these in WSGI file.
"""
import os

def configure_production():
    """Set production environment variables if not already set"""
    
    # Ensure critical settings are present
    if not os.environ.get('SECRET_KEY'):
        print("WARNING: SECRET_KEY not set in environment!")
    
    if not os.environ.get('LOGBERT_API_KEYS'):
        print("WARNING: LOGBERT_API_KEYS not set in environment!")
    
    # Set production defaults
    os.environ.setdefault('DEBUG', 'False')
    
    return {
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
        'DEBUG': os.environ.get('DEBUG', 'False') == 'True',
        'ALLOWED_HOSTS': os.environ.get('ALLOWED_HOSTS', '').split(','),
        'LOGBERT_API_KEYS': os.environ.get('LOGBERT_API_KEYS', '').split(','),
        'CORS_ALLOWED_ORIGINS': os.environ.get('CORS_ALLOWED_ORIGINS', '').split(','),
    }
```

## 📋 DEPLOYMENT CHECKLIST

### Before Upload:

- [ ] Update `settings.py` with environment variable support
- [ ] Add `STATIC_ROOT` to settings
- [ ] Remove obsolete settings (Channels, Kafka, Celery)
- [ ] Create `requirements-pythonanywhere.txt` with minimal deps
- [ ] Create `.gitignore` file
- [ ] Generate production API keys
- [ ] Generate production SECRET_KEY
- [ ] Test locally with production-like settings

### On PythonAnywhere:

- [ ] Upload code (via Git or file upload)
- [ ] Create virtualenv
- [ ] Install from `requirements-pythonanywhere.txt`
- [ ] Set environment variables in WSGI file
- [ ] Run `python manage.py collectstatic`
- [ ] Run `python manage.py migrate`
- [ ] Create superuser
- [ ] Configure web app settings
- [ ] Set static files mapping
- [ ] Test API endpoints

## 🚨 SECURITY WARNINGS

### DO NOT upload these files:

- ❌ `.env` (if it exists with real keys)
- ❌ `db.sqlite3` (if it has test data)
- ❌ `logs/` directory (may contain sensitive info)
- ❌ Any files with hardcoded passwords/keys

### MUST generate new keys for production:

```bash
# Generate new SECRET_KEY
python -c 'import secrets; print(secrets.token_urlsafe(50))'

# Generate API keys (create 2-3 for redundancy)
python -c 'import secrets; print(secrets.token_urlsafe(32))'
python -c 'import secrets; print(secrets.token_urlsafe(32))'
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

## 📊 ESTIMATED DEPLOYMENT TIME

With fixes: **30-45 minutes**

Breakdown:
- Code fixes: 15 minutes
- Upload to PythonAnywhere: 5 minutes
- Setup virtualenv & install: 10 minutes
- Configure WSGI & environment: 10 minutes
- Run migrations & test: 10 minutes

## 🎯 SUMMARY

### Current Status: ❌ NOT READY

**Critical blockers:**
1. Hardcoded SECRET_KEY in settings.py
2. DEBUG=True (security risk)
3. No environment variable support
4. Missing STATIC_ROOT
5. Bloated requirements.txt with unnecessary packages

**After fixing these issues:** ✅ READY TO DEPLOY

The code structure is solid, but configuration needs to be production-ready.

---

## 🛠️ QUICK FIX COMMANDS

I can help you fix these issues right now. Would you like me to:

1. Update `settings.py` with environment variable support?
2. Add `STATIC_ROOT` configuration?
3. Create minimal `requirements-pythonanywhere.txt`?
4. Remove obsolete settings (Channels, Kafka, Celery)?
5. Create `.gitignore` file?

Let me know and I'll make these changes immediately!
