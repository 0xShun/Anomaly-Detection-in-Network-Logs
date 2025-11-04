# PythonAnywhere Deployment Guide

This guide covers deploying the LogBERT web platform to PythonAnywhere for remote monitoring.

## Architecture Overview

```
┌─────────────────────────────────────┐
│    Local School Network             │
│                                     │
│  ┌──────────────────────────────┐  │
│  │ LogBERT Analysis Pipeline    │  │
│  │ - Log parsing (Drain)        │  │
│  │ - Model inference            │  │
│  │ - Anomaly detection          │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│             │ Push sanitized data   │
│             │ (local_network_pusher.py)
│             │                       │
└─────────────┼───────────────────────┘
              │
              │ HTTPS + API Key Auth
              ▼
┌─────────────────────────────────────┐
│    PythonAnywhere                   │
│                                     │
│  ┌──────────────────────────────┐  │
│  │ Django Web Application       │  │
│  │ - REST API endpoints         │  │
│  │ - Web dashboard              │  │
│  │ - SQLite database            │  │
│  └──────────────────────────────┘  │
│                                     │
│  Accessible from anywhere           │
└─────────────────────────────────────┘
```

## Prerequisites

1. PythonAnywhere account (free or paid)
2. API keys generated for authentication
3. LogBERT analysis running on local network

## Step 1: Prepare Your Code

1. **Generate API Keys**
   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(32))'
   ```
   Save this key securely - you'll need it for both PythonAnywhere and local network.

2. **Update settings**
   - Copy `.env.template` to `.env`
   - Fill in your values (API keys, domain, etc.)

## Step 2: Upload to PythonAnywhere

### Option A: Git (Recommended)

1. Push your `webplatform/` directory to a Git repository
2. On PythonAnywhere, open a Bash console:
   ```bash
   git clone https://github.com/yourusername/logbert-webplatform.git
   cd logbert-webplatform
   ```

### Option B: Direct Upload

1. Zip the `webplatform/` directory
2. Upload via PythonAnywhere Files tab
3. Unzip in your home directory

## Step 3: Set Up Virtual Environment

In PythonAnywhere Bash console:

```bash
# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.10 logbert-env

# Activate it
workon logbert-env

# Install dependencies
cd ~/webplatform  # or your path
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

PythonAnywhere doesn't use .env files directly. Set environment variables in the WSGI file.

**Files** → **WSGI configuration file** → Edit:

```python
import os
import sys

# Add your project directory to path
path = '/home/yourusername/webplatform'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'webplatform.settings'
os.environ['SECRET_KEY'] = 'your-secret-key-here'
os.environ['DEBUG'] = 'False'
os.environ['LOGBERT_API_KEYS'] = 'your-api-key-1,your-api-key-2'

# Initialize Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## Step 5: Database Setup

In PythonAnywhere Bash console:

```bash
cd ~/webplatform
workon logbert-env

# Create database tables
python manage.py makemigrations
python manage.py migrate

# Create admin superuser
python manage.py createsuperuser
```

## Step 6: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

## Step 7: Configure Web App

1. Go to **Web** tab on PythonAnywhere
2. Click **Add a new web app**
3. Choose **Manual configuration**
4. Select Python 3.10
5. Set:
   - **Source code**: `/home/yourusername/webplatform`
   - **Working directory**: `/home/yourusername/webplatform`
   - **Virtualenv**: `/home/yourusername/.virtualenvs/logbert-env`

6. **Static files mapping**:
   - URL: `/static/`
   - Directory: `/home/yourusername/webplatform/static`

7. Click **Reload** to start your app

## Step 8: Configure Local Network Pusher

On your local school network server:

1. **Install dependencies**:
   ```bash
   pip install requests
   ```

2. **Set environment variables**:
   ```bash
   export LOGBERT_API_KEY="your-api-key-here"
   export LOGBERT_REMOTE_URL="https://yourschool.pythonanywhere.com"
   ```

3. **Test the pusher**:
   ```bash
   python local_network_pusher.py --school-id university_main --health-check-only
   ```

4. **Set up cron job** (run every 5 minutes):
   ```bash
   crontab -e
   ```
   
   Add:
   ```
   */5 * * * * cd /opt/logbert && /usr/bin/python3 local_network_pusher.py --school-id university_main >> /var/log/logbert-pusher.log 2>&1
   ```

## Step 9: Test the API

Test from your local network:

```bash
# Test health check
curl -X POST https://yourschool.pythonanywhere.com/api/v1/health/ \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"school_id":"test","status":"ok"}'

# Test alert submission
curl -X POST https://yourschool.pythonanywhere.com/api/v1/alerts/ \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-11-04T10:30:00Z",
    "school_id": "university_main",
    "alert_level": "high",
    "anomaly_score": 0.89,
    "affected_systems": ["auth_server"],
    "summary": "Test alert",
    "log_count": 100
  }'
```

## Step 10: Access the Dashboard

1. Go to `https://yourschool.pythonanywhere.com/admin/`
2. Log in with your superuser credentials
3. Navigate to the dashboard

## Security Best Practices

### 1. API Key Security
- ✅ Store API keys in environment variables only
- ✅ Never commit API keys to Git
- ✅ Use different keys for dev/production
- ✅ Rotate keys periodically (every 90 days)

### 2. HTTPS Only
- ✅ PythonAnywhere provides SSL automatically
- ✅ Ensure local pusher uses HTTPS URLs

### 3. Data Sanitization
- ✅ Never send raw logs with PII
- ✅ Only send aggregated metrics and alerts
- ✅ Review `_sanitize_alert()` in pusher script

### 4. Access Control
- ✅ Use Django admin for user management
- ✅ Only create admin users (no public registration)
- ✅ Use strong passwords

### 5. Rate Limiting
Consider adding rate limiting if needed:
```bash
pip install django-ratelimit
```

## Monitoring

### View Logs on PythonAnywhere
- **Error log**: Web tab → Log files → Error log
- **Server log**: Web tab → Log files → Server log

### Monitor Local Pusher
```bash
tail -f /var/log/logbert-pusher.log
```

## Troubleshooting

### API Returns 401 Unauthorized
- Check API key is set correctly in environment
- Verify key matches between local and remote
- Check Authorization header format: `Bearer <key>`

### CORS Errors
- Add your school network IP/domain to `CORS_ALLOWED_ORIGINS` in settings
- Check network firewall allows outbound HTTPS

### Database Locked
- SQLite can handle PythonAnywhere traffic
- If issues, consider upgrading to PostgreSQL (free tier available)

### Static Files Not Loading
- Run `python manage.py collectstatic` again
- Check static files mapping in Web tab

## Updating the Application

When you make changes:

```bash
# On PythonAnywhere
cd ~/webplatform
git pull  # if using Git
workon logbert-env
pip install -r requirements.txt --upgrade
python manage.py migrate
python manage.py collectstatic --noinput

# Reload the web app
# Web tab → Reload button
```

## Backup

Regular backups of your database:

```bash
# Backup script
cd ~/webplatform
cp db.sqlite3 backups/db_$(date +%Y%m%d).sqlite3
```

Add to cron:
```
0 2 * * * cd ~/webplatform && cp db.sqlite3 backups/db_$(date +\%Y\%m\%d).sqlite3
```

## Support

- Django docs: https://docs.djangoproject.com/
- DRF docs: https://www.django-rest-framework.org/
- PythonAnywhere help: https://help.pythonanywhere.com/
