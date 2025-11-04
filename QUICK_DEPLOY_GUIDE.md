# Quick PythonAnywhere Deployment Guide

**Updated for production-ready configuration**

## Pre-Deployment Checklist

✅ All security issues fixed:
- Environment variable support added to settings.py
- STATIC_ROOT configured
- Obsolete settings removed (Kafka, Celery, Channels)
- Minimal requirements file created
- .gitignore file created

## Step-by-Step Deployment

### 1. Generate Production Keys

On your local machine:

```bash
cd /home/shun/Desktop/logbert/webplatform
python -m webplatform.production_settings
```

This will generate:
- SECRET_KEY (50 chars)
- API keys (32 chars each) - generate 2-3

**Save these keys securely!** You'll need them for the WSGI file.

### 2. Prepare Code for Upload

**Option A: Using Git (Recommended)**

```bash
cd /home/shun/Desktop/logbert
git add webplatform/
git commit -m "Production-ready configuration for PythonAnywhere"
git push
```

**Option B: Direct File Upload**

ZIP the webplatform folder and upload via PythonAnywhere Files tab.

### 3. On PythonAnywhere - Upload Code

1. Log in to PythonAnywhere
2. Go to **Files** tab
3. Navigate to `/home/yourusername/`
4. Create directory: `logbert`
5. Upload/clone your code to `/home/yourusername/logbert/webplatform/`

### 4. Create Virtual Environment

In PythonAnywhere **Bash console**:

```bash
cd ~
mkvirtualenv --python=/usr/bin/python3.10 logbert-env
```

### 5. Install Dependencies

```bash
cd ~/logbert/webplatform
pip install -r requirements-pythonanywhere.txt
```

**Note:** We're using `requirements-pythonanywhere.txt` (not requirements.txt) to avoid installing PyTorch and other heavy packages.

### 6. Configure Web App

Go to **Web** tab:

1. Click "Add a new web app"
2. Choose "Manual configuration"
3. Select Python 3.10
4. Note your domain: `yourusername.pythonanywhere.com`

### 7. Edit WSGI File

In **Web** tab, click on WSGI configuration file link.

**Delete everything** and paste this (modify the values):

```python
import os
import sys

# Add project to path (change 'yourusername')
path = '/home/yourusername/logbert/webplatform'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables - USE YOUR GENERATED KEYS
os.environ['SECRET_KEY'] = 'paste-your-50-char-secret-key-here'
os.environ['DEBUG'] = 'False'
os.environ['ALLOWED_HOSTS'] = 'yourusername.pythonanywhere.com'
os.environ['LOGBERT_API_KEYS'] = 'key1,key2,key3'
os.environ['CORS_ALLOWED_ORIGINS'] = 'https://yourschool.edu,http://192.168.1.100'

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webplatform.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Replace:**
- `yourusername` with your PythonAnywhere username
- `paste-your-50-char-secret-key-here` with your generated SECRET_KEY
- `key1,key2,key3` with your generated API keys
- `yourschool.edu` and IP with your actual network addresses

Click **Save**.

### 8. Configure Virtualenv

In **Web** tab:

1. Find "Virtualenv" section
2. Enter: `/home/yourusername/.virtualenvs/logbert-env`
3. Click the checkmark to save

### 9. Run Database Migrations

In **Bash console**:

```bash
cd ~/logbert/webplatform
workon logbert-env
python manage.py migrate
```

Expected output:
```
Operations to perform:
  Apply all migrations: admin, api, auth, contenttypes, sessions, ...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
```

### 10. Create Superuser

```bash
python manage.py createsuperuser
```

Enter:
- Username: admin
- Email: your-email@example.com
- Password: (choose a strong password)

### 11. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

This creates `/home/yourusername/logbert/webplatform/staticfiles/`

### 12. Configure Static Files Mapping

In **Web** tab, scroll to "Static files" section:

Add mapping:
- URL: `/static/`
- Directory: `/home/yourusername/logbert/webplatform/staticfiles/`

Click checkmark to save.

### 13. Reload Web App

In **Web** tab, click the big green **"Reload yourusername.pythonanywhere.com"** button.

### 14. Test Your Deployment

**Test 1: Check Status Endpoint**

```bash
curl https://yourusername.pythonanywhere.com/api/v1/status/
```

Expected: `{"status": "ok", "message": "LogBERT API is running", ...}`

**Test 2: Test Authentication**

```bash
curl -X POST https://yourusername.pythonanywhere.com/api/v1/health/ \
  -H "Authorization: Bearer YOUR-API-KEY" \
  -H "Content-Type: application/json" \
  -d '{"school_id":"test","status":"healthy"}'
```

Expected: `{"message": "Health check received", ...}`

**Test 3: Access Admin**

Open in browser: `https://yourusername.pythonanywhere.com/admin`

Login with your superuser credentials.

### 15. Run Comprehensive Tests

On your **local machine**:

```bash
cd /home/shun/Desktop/logbert/webplatform
export LOGBERT_API_KEY="your-api-key-from-step-1"
export LOGBERT_REMOTE_URL="https://yourusername.pythonanywhere.com"
python comprehensive_api_test.py
```

All tests should pass!

## Configure Local Network Pusher

On your **school's local network** (where LogBERT runs):

### 1. Set Environment Variables

```bash
export LOGBERT_API_KEY="your-api-key-from-pythonanywhere"
export LOGBERT_REMOTE_URL="https://yourusername.pythonanywhere.com"
```

### 2. Test Pusher

```bash
cd /home/shun/Desktop/logbert
python local_network_pusher.py --school-id "school-001" --health-check-only
```

Expected: Health check successful

### 3. Set Up Cron Job

```bash
crontab -e
```

Add:
```bash
# Push LogBERT data every 5 minutes
*/5 * * * * cd /path/to/logbert && /path/to/venv/bin/python local_network_pusher.py --school-id "school-001" --output-dir ./output >> /var/log/logbert_pusher.log 2>&1
```

Save and exit.

## Troubleshooting

### Issue: "DisallowedHost at /"

**Solution:** Add your domain to ALLOWED_HOSTS in WSGI file:
```python
os.environ['ALLOWED_HOSTS'] = 'yourusername.pythonanywhere.com'
```

### Issue: "401 Unauthorized" when testing API

**Solution:** Check API key matches WSGI file:
```bash
# In WSGI file
os.environ['LOGBERT_API_KEYS'] = 'key1,key2,key3'

# In test
export LOGBERT_API_KEY="key1"  # Use one of the keys
```

### Issue: Static files not loading

**Solution:** 
1. Run `python manage.py collectstatic`
2. Check static files mapping in Web tab
3. Reload web app

### Issue: "500 Internal Server Error"

**Solution:**
1. Check error log in Web tab
2. Verify all environment variables set in WSGI
3. Check virtualenv path is correct
4. Run `python manage.py check` in console

### Issue: CORS errors from local network

**Solution:** Add your network IP to CORS_ALLOWED_ORIGINS in WSGI:
```python
os.environ['CORS_ALLOWED_ORIGINS'] = 'http://192.168.1.100:8000,http://10.0.0.5:8000'
```

## Post-Deployment Checklist

- [ ] Status endpoint returns 200 OK
- [ ] Can login to admin interface
- [ ] Health check endpoint works with API key
- [ ] Can create alert via API
- [ ] Comprehensive tests pass from local machine
- [ ] Local pusher can send health check
- [ ] Static files load correctly
- [ ] No errors in PythonAnywhere error log
- [ ] Cron job configured on local network

## Security Reminders

- ✅ Never commit .env file to Git
- ✅ Use different SECRET_KEY and API keys for production
- ✅ Keep DEBUG=False in production
- ✅ Rotate API keys periodically
- ✅ Monitor PythonAnywhere logs regularly
- ✅ Use HTTPS only (PythonAnywhere provides this)

## Monitoring

Check these regularly:
- **Error log**: Web tab → Error log link
- **Server log**: Web tab → Server log link  
- **API usage**: Check Django admin → API models

## Next Steps

1. Update DEPLOYMENT.md with your actual domain/IPs
2. Document your API keys securely (password manager)
3. Share API endpoint with monitoring team
4. Set up alerting if needed
5. Plan regular data cleanup (old logs, alerts)

## Success! 🎉

Your LogBERT Remote Monitoring Platform is now live on PythonAnywhere!

Access points:
- **Admin**: https://yourusername.pythonanywhere.com/admin
- **API Status**: https://yourusername.pythonanywhere.com/api/v1/status/
- **API Docs**: See TESTING_GUIDE.md for all endpoints

The local network can now push data to your remote platform 24/7!
