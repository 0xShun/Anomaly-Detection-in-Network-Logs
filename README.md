# LogBERT Remote Monitoring Platform

A Django-based web platform for monitoring LogBERT anomaly detection results remotely. Designed for deployment on PythonAnywhere to provide secure, internet-accessible monitoring for school network administrators.

## Features

### ✅ REST API for Data Ingestion

-   **API Key Authentication**: Secure endpoints using Bearer token authentication
-   **Alert Management**: Receive and store anomaly alerts from local network
-   **System Metrics**: Track CPU, memory, processing times
-   **Log Statistics**: Monitor parsing coverage, templates, throughput
-   **Raw Model Outputs**: Store detailed model inference results for analysis

### ✅ Web Dashboard

-   **Admin Interface**: Django admin for managing all data
-   **Alert Monitoring**: View and manage security alerts
-   **Performance Tracking**: Monitor system health and processing metrics
-   **Data Visualization**: Charts and graphs for trend analysis

### ✅ Security & Authentication

-   **API Key Authentication**: Environment-based key management
-   **Django Admin Auth**: Username/password for dashboard access
-   **CORS Protection**: Configurable allowed origins
-   **HTTPS Only**: SSL provided by PythonAnywhere

## Architecture

```
Local School Network          →  Internet  →  PythonAnywhere
─────────────────────                         ──────────────
LogBERT Analysis                              Django Web App
- Log parsing (Drain)                         - REST API endpoints
- Model inference                             - Web dashboard
- Anomaly detection                           - SQLite database
                                              
local_network_pusher.py  ─────HTTPS + API Key───→  /api/v1/*
(cron job every 5 min)                        
```

### Technology Stack

-   **Backend**: Django 5.2.5 with Django REST Framework
-   **Database**: SQLite (PythonAnywhere compatible)
-   **Authentication**: API keys (environment variables) + Django sessions
-   **Deployment**: PythonAnywhere (WSGI)
-   **CORS**: django-cors-headers for cross-origin API requests
-   **Cache**: Redis for session and channel layer storage

## Prerequisites

-   Python 3.8+
-   SQLite (included with Python)
-   PythonAnywhere account (for deployment)

## Installation

### Local Development Setup

1. **Install dependencies**

    ```bash
    cd /path/to/logbert/webplatform
    pip install -r requirements.txt
    ```

2. **Configure environment variables**
   
   Copy the template:
   ```bash
   cp .env.template .env
   ```
   
   Edit `.env` and set:
   ```env
   SECRET_KEY=your-secret-key-here  # Generate: python -c 'import secrets; print(secrets.token_urlsafe(50))'
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   LOGBERT_API_KEYS=key1,key2,key3  # Generate: python -c 'import secrets; print(secrets.token_urlsafe(32))'
   CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
   ```

3. **Run database migrations**

    ```bash
    python manage.py makemigrations api
    python manage.py migrate
    ```

4. **Create Django admin user**

    ```bash
    python manage.py createsuperuser
    ```

5. **Test the API locally**

    ```bash
    python manage.py runserver
    ```
    
    Then in another terminal:
    ```bash
    python test_api.py
    ```

### PythonAnywhere Deployment

**See [DEPLOYMENT.md](DEPLOYMENT.md) for complete step-by-step deployment instructions.**

Quick steps:
1. Upload code via Git or file upload
2. Create virtualenv: `mkvirtualenv --python=/usr/bin/python3.10 logbert-env`
3. Install requirements: `pip install -r requirements.txt`
4. Edit WSGI file with environment variables
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Configure static files
8. Reload web app

### Local Network Configuration

**Configure the pusher script on your school's LogBERT system:**

1. **Set environment variables on local machine:**
   ```bash
   export LOGBERT_API_KEY="your-api-key-from-pythonanywhere"
   export LOGBERT_REMOTE_URL="https://yourusername.pythonanywhere.com"
   ```

2. **Test the pusher manually:**
   ```bash
   cd /path/to/logbert
   python local_network_pusher.py --school-id "school-001" --output-dir "./output"
   ```

3. **Set up cron job** (run every 5 minutes):
   ```bash
   crontab -e
   # Add this line:
   */5 * * * * cd /path/to/logbert && /path/to/venv/bin/python local_network_pusher.py --school-id "school-001" >> /var/log/logbert_pusher.log 2>&1
   ```

## Usage

### 1. Access the Platform

**Web Dashboard:**
-   Navigate to `https://yourusername.pythonanywhere.com/admin`
-   Login with your Django superuser credentials
-   View and manage alerts, metrics, statistics, and raw outputs

**API Access:**
-   Base URL: `https://yourusername.pythonanywhere.com/api/v1/`
-   Authentication: Include `Authorization: Bearer YOUR_API_KEY` header
-   Available endpoints documented below

### 2. Send Data from Local Network

Run the pusher script on your school's LogBERT system:

```bash
python local_network_pusher.py --school-id "school-001" --output-dir "./output"
```

This will:
- Read LogBERT analysis results from the output directory
- Sanitize sensitive data (remove PII, IP addresses, etc.)
- Push alerts, metrics, statistics, and raw outputs to the remote API
- Log all operations for debugging

### 3. Monitor via Dashboard

-   View alerts by severity (low, medium, high, critical)
-   Track system performance metrics (CPU, memory, processing time)
-   Analyze log statistics (parsing coverage, templates, throughput)
-   Inspect raw model outputs (attention weights, anomaly scores)

## API Endpoints

### Data Ingestion (POST)

All endpoints require `Authorization: Bearer YOUR_API_KEY` header.

-   `POST /api/v1/alerts/` - Create new anomaly alert
-   `POST /api/v1/metrics/` - Submit system metric
-   `POST /api/v1/statistics/` - Upload log statistics
-   `POST /api/v1/raw-outputs/` - Store raw model output

### Data Retrieval (GET)

-   `GET /api/v1/alerts/` - List all alerts (filter by `?school_id=`, `?level=`, `?status=`)
-   `GET /api/v1/metrics/` - List metrics (filter by `?school_id=`, `?metric_type=`)
-   `GET /api/v1/statistics/` - List statistics (filter by `?school_id=`)
-   `GET /api/v1/raw-outputs/` - List raw outputs (filter by `?school_id=`)

### System Status

-   `GET /api/v1/status/` - API health and version information
-   `POST /api/v1/health/` - Health check endpoint for monitoring

### Testing API

Use the included test script:

```bash
cd /path/to/logbert/webplatform
export LOGBERT_API_KEY="your-api-key"
export LOGBERT_REMOTE_URL="https://yourusername.pythonanywhere.com"
python test_api.py
```

## Configuration

### Environment Variables

Key configuration in `.env` file or PythonAnywhere WSGI:

```python
# Django Core
SECRET_KEY = 'your-secret-key-here'
DEBUG = False  # True for local dev, False for production
ALLOWED_HOSTS = 'yourusername.pythonanywhere.com,localhost'

# API Authentication
LOGBERT_API_KEYS = 'key1,key2,key3'  # Comma-separated API keys

# CORS Configuration
CORS_ALLOWED_ORIGINS = 'http://192.168.1.100:8000,http://10.0.0.5:8000'  # Your school network IPs
```

### Django REST Framework Settings

Configured in `webplatform/settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'api.authentication.APIKeyAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'PAGE_SIZE': 100,
}
```

## Project Structure

```
webplatform/
├── api/                      # REST API for data ingestion
│   ├── models.py            # Alert, SystemMetric, LogStatistic, RawModelOutput
│   ├── views.py             # API ViewSets and endpoints
│   ├── serializers.py       # DRF serializers
│   ├── authentication.py    # API key authentication
│   └── admin.py             # Django admin configuration
├── authentication/          # User authentication
├── dashboard/              # Web dashboard views
├── monitoring/             # System monitoring
├── analytics/              # Data visualization
├── templates/              # HTML templates
├── static/                 # Static files (CSS, JS)
├── webplatform/            # Django project settings
│   ├── settings.py         # Main configuration
│   └── urls.py             # URL routing
├── test_api.py             # API testing script
├── DEPLOYMENT.md           # Deployment guide
└── manage.py               # Django management

local_network_pusher.py     # Script to push data from local network (in parent directory)
```

## Development Workflow

### Adding API Features

1. Add model in `api/models.py`
2. Create serializer in `api/serializers.py`
3. Add ViewSet in `api/views.py`
4. Register in `api/admin.py` for Django admin
5. Run migrations: `python manage.py makemigrations api && python manage.py migrate`
6. Update `local_network_pusher.py` to send new data type

### Testing Changes

1. Test locally: `python manage.py runserver`
2. Run API tests: `python test_api.py`
3. Check Django admin: http://localhost:8000/admin
4. Deploy to PythonAnywhere following DEPLOYMENT.md

## Troubleshooting

### API Issues

1. **Authentication Failed (401)**
   - Check API key is correctly set in environment variables
   - Verify header format: `Authorization: Bearer YOUR_API_KEY`
   - Ensure API key is in `LOGBERT_API_KEYS` on server

2. **CORS Errors**
   - Add your local network IP to `CORS_ALLOWED_ORIGINS` in settings.py
   - Restart Django server after configuration changes
   - Check browser console for specific CORS error details

3. **Database Migration Errors**
   - Run: `python manage.py makemigrations api`
   - Then: `python manage.py migrate`
   - If issues persist, delete `db.sqlite3` and re-run migrations

4. **Local Pusher Not Sending Data**
   - Check environment variables: `echo $LOGBERT_API_KEY`
   - Test network connectivity: `curl https://yourusername.pythonanywhere.com/api/v1/status/`
   - Review pusher logs: `tail -f /var/log/logbert_pusher.log`
   - Verify output directory contains LogBERT results

### PythonAnywhere Deployment Issues

1. **500 Internal Server Error**
   - Check error log in PythonAnywhere web tab
   - Verify all environment variables are set in WSGI file
   - Ensure virtualenv has all requirements installed
   - Run migrations: `python manage.py migrate`

2. **Static Files Not Loading**
   - Run: `python manage.py collectstatic`
   - Configure static files mapping in PythonAnywhere web tab
   - URL: `/static/`, Directory: `/home/yourusername/logbert/webplatform/staticfiles/`

3. **Database Locked Errors**
   - SQLite limitation with concurrent writes
   - Ensure only one process writes at a time
   - Consider batch inserts in pusher script

### Logs and Debugging

-   **PythonAnywhere Error Log**: Web tab → Error log link
-   **PythonAnywhere Server Log**: Web tab → Server log link
-   **Local Pusher Log**: `/var/log/logbert_pusher.log` (if configured in cron)
-   **Django Debug Mode**: Set `DEBUG=True` in `.env` (local only!)
-   **API Test**: `python test_api.py` to validate all endpoints

## Security Considerations

- **Never commit API keys** to version control (use `.gitignore` for `.env`)
- **Use HTTPS only** in production (PythonAnywhere provides this)
- **Rotate API keys** periodically
- **Sanitize data** before transmission (pusher script does this)
- **Limit CORS origins** to only your school network IPs
- **Keep Django SECRET_KEY secret** and never share it

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)**: Complete PythonAnywhere deployment guide
- **Django REST Framework**: https://www.django-rest-framework.org/
- **PythonAnywhere Help**: https://help.pythonanywhere.com/
- **LogBERT Paper**: [Original research paper link]

## Support

For issues and questions:
- Check the troubleshooting section above
- Review `DEPLOYMENT.md` for deployment-specific issues
- Inspect logs (see Logs and Debugging section)
- Test API with `test_api.py`
