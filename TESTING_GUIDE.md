# Testing Guide for LogBERT Remote Monitoring Platform

This guide provides step-by-step instructions for testing the API before deployment.

## Overview

We've created three comprehensive testing tools:

1. **validate_setup.py** - Pre-flight checks (configuration, database, dependencies)
2. **comprehensive_api_test.py** - Full API endpoint testing with detailed reports
3. **quick_setup_test.sh** - Automated setup script that prepares everything

## Quick Start (Recommended)

The fastest way to set up and test everything:

```bash
cd /home/shun/Desktop/logbert/webplatform
./quick_setup_test.sh
```

This script will:
- ✅ Check Python version
- ✅ Install dependencies from requirements.txt
- ✅ Create .env file with generated SECRET_KEY and API keys
- ✅ Run database migrations
- ✅ Create admin user (username: admin, password: admin123)
- ✅ Collect static files
- ✅ Run validation checks
- ✅ Set up test environment variables

After running this, follow the "Next steps" printed at the end.

## Manual Testing Workflow

### Step 1: Environment Setup

Create and configure your `.env` file:

```bash
cd /home/shun/Desktop/logbert/webplatform
cp .env.template .env
```

Generate secure keys:

```bash
# Generate SECRET_KEY
python -c 'import secrets; print(secrets.token_urlsafe(50))'

# Generate API keys (create 2-3 for testing)
python -c 'import secrets; print(secrets.token_urlsafe(32))'
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Edit `.env` and add the generated values:

```env
SECRET_KEY=<your-generated-secret-key>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
LOGBERT_API_KEYS=<key1>,<key2>,<key3>
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Expected packages:
- Django 5.2.5
- djangorestframework 3.14.0
- django-cors-headers 4.3.1
- requests (for testing scripts)

### Step 3: Database Setup

Create and apply migrations:

```bash
python manage.py makemigrations api
python manage.py migrate
```

Expected output:
```
Migrations for 'api':
  api/migrations/0001_initial.py
    - Create model Alert
    - Create model SystemMetric
    - Create model LogStatistic
    - Create model RawModelOutput
```

### Step 4: Create Admin User

```bash
python manage.py createsuperuser
```

Enter:
- Username: admin
- Email: admin@example.com
- Password: (choose a secure password)

### Step 5: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Step 6: Run Pre-Flight Validation

Run the comprehensive validation script:

```bash
python validate_setup.py
```

This checks:
- ✅ Environment variables (SECRET_KEY, API_KEYS)
- ✅ Database connection and migrations
- ✅ Installed apps (api, rest_framework, corsheaders)
- ✅ API configuration (authentication, pagination, CORS)
- ✅ URL configuration
- ✅ Dependencies
- ✅ Static files
- ✅ Admin user
- ✅ API key format
- ✅ Local pusher script
- ✅ (Optional) Django test suite

**Expected result**: All checks should pass (green ✓)

If any check fails (red ✗), fix the issue before proceeding.

### Step 7: Start Development Server

```bash
python manage.py runserver
```

Server should start on http://localhost:8000

**Manual verification**:
1. Open browser to http://localhost:8000/admin
2. Login with your superuser credentials
3. You should see the Django admin interface

### Step 8: Run Django Unit Tests

In a new terminal (keep server running):

```bash
cd /home/shun/Desktop/logbert/webplatform
python manage.py test api --verbosity=2
```

This runs comprehensive unit tests covering:
- Model creation and validation
- API authentication (valid, invalid, missing keys)
- Alert CRUD operations and filtering
- Metric CRUD operations and filtering
- Statistic CRUD operations
- Raw output CRUD operations
- Pagination
- Data validation

**Expected result**: All tests should pass

Example output:
```
test_alert_creation (api.tests.ModelTests) ... ok
test_alert_status_transitions (api.tests.ModelTests) ... ok
test_valid_api_key_bearer (api.tests.AuthenticationTests) ... ok
...
----------------------------------------------------------------------
Ran 30 tests in 5.234s

OK
```

### Step 9: Run Comprehensive API Tests

Set up environment variables for testing:

```bash
export LOGBERT_API_KEY="your-api-key-here"  # Use one from your .env
export LOGBERT_REMOTE_URL="http://localhost:8000"
```

Run the comprehensive test suite:

```bash
python comprehensive_api_test.py
```

This performs:
- **Authentication Tests**: Valid/invalid/missing API keys
- **Status Endpoints**: GET /status/, POST /health/
- **Alert CRUD**: Create, list, filter by level/school/status
- **Metric CRUD**: Create, list, filter by type
- **Statistic CRUD**: Create with JSON fields, list
- **Raw Output CRUD**: Create with complex data, list, filter
- **Pagination**: Multiple pages, next/previous links

**Expected result**: 30+ tests pass with detailed output

Example output:
```
╔════════════════════════════════════════════════════════════════════╗
║  LogBERT Remote Monitoring API - Comprehensive Test Suite         ║
╚════════════════════════════════════════════════════════════════════╝

==================================================================
1. AUTHENTICATION TESTS
==================================================================

1.1. Valid API Key (Bearer token)
  ✓ PASS: Authentication successful with valid API key

1.2. Invalid API Key
  ✓ PASS: Correctly rejected invalid API key (401)

...

==================================================================
TEST SUMMARY
==================================================================

Total Tests:  32
Passed:       32
Failed:       0
Pass Rate:    100.0%
Duration:     3.45 seconds

✓ ALL TESTS PASSED!

The API is working correctly and ready for deployment.
```

### Step 10: Test Local Pusher Script

Test the data pusher from local network:

```bash
cd /home/shun/Desktop/logbert
export LOGBERT_API_KEY="your-api-key-here"
export LOGBERT_REMOTE_URL="http://localhost:8000"

# Create sample output directory if it doesn't exist
mkdir -p output/test_data

# Run pusher in health check mode
python local_network_pusher.py --school-id test-school --health-check-only

# Run full pusher (requires actual LogBERT output files)
python local_network_pusher.py --school-id test-school --output-dir output
```

**Expected result**: 
- Health check should return "healthy" status
- Full run should push data and log success messages

Check Django admin to verify data was received:
```bash
# Open browser
http://localhost:8000/admin/api/alert/
http://localhost:8000/admin/api/systemmetric/
http://localhost:8000/admin/api/logstatistic/
http://localhost:8000/admin/api/rawmodeloutput/
```

### Step 11: Manual API Testing with curl

Test individual endpoints manually:

```bash
# Set variables
API_KEY="your-api-key-here"
BASE_URL="http://localhost:8000"

# Test status endpoint
curl -X GET "$BASE_URL/api/v1/status/" \
  -H "Authorization: Bearer $API_KEY"

# Create an alert
curl -X POST "$BASE_URL/api/v1/alerts/" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "school_id": "test-001",
    "alert_type": "anomaly_detected",
    "message": "Test anomaly from curl",
    "level": "high",
    "anomaly_score": 0.95,
    "affected_systems": "server-01",
    "status": "active"
  }'

# List alerts
curl -X GET "$BASE_URL/api/v1/alerts/" \
  -H "Authorization: Bearer $API_KEY"

# Filter alerts by level
curl -X GET "$BASE_URL/api/v1/alerts/?level=high" \
  -H "Authorization: Bearer $API_KEY"

# Create a metric
curl -X POST "$BASE_URL/api/v1/metrics/" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "school_id": "test-001",
    "metric_type": "cpu_usage",
    "value": 75.5,
    "unit": "percent",
    "source": "server-01"
  }'

# List metrics
curl -X GET "$BASE_URL/api/v1/metrics/" \
  -H "Authorization: Bearer $API_KEY"
```

## Testing Checklist

Use this checklist to ensure everything is working:

### Configuration
- [ ] `.env` file created with all required variables
- [ ] SECRET_KEY generated and set
- [ ] LOGBERT_API_KEYS generated (2-3 keys for testing)
- [ ] DEBUG=True for local testing
- [ ] ALLOWED_HOSTS includes localhost
- [ ] CORS_ALLOWED_ORIGINS configured

### Database
- [ ] Migrations created (`makemigrations api`)
- [ ] Migrations applied (`migrate`)
- [ ] All 4 tables exist (alert, systemmetric, logstatistic, rawmodeloutput)
- [ ] Database can be queried without errors

### Admin
- [ ] Superuser created
- [ ] Can login to /admin
- [ ] All 4 API models visible in admin
- [ ] Can view and manage records

### API Endpoints
- [ ] GET /api/v1/status/ returns 200
- [ ] POST /api/v1/health/ returns 200
- [ ] POST /api/v1/alerts/ creates alert (201)
- [ ] GET /api/v1/alerts/ lists alerts (200)
- [ ] Filtering works (?level=high, ?school_id=X)
- [ ] POST /api/v1/metrics/ creates metric (201)
- [ ] GET /api/v1/metrics/ lists metrics (200)
- [ ] POST /api/v1/statistics/ creates statistic (201)
- [ ] GET /api/v1/statistics/ lists statistics (200)
- [ ] POST /api/v1/raw-outputs/ creates output (201)
- [ ] GET /api/v1/raw-outputs/ lists outputs (200)

### Authentication
- [ ] Valid API key is accepted
- [ ] Invalid API key returns 401
- [ ] Missing API key returns 401
- [ ] Bearer token format works
- [ ] X-API-Key header format works

### Data Pusher
- [ ] Health check works
- [ ] Can push alerts
- [ ] Can push metrics
- [ ] Can push statistics
- [ ] Can push raw outputs
- [ ] Data sanitization works
- [ ] Errors are logged

### Test Suites
- [ ] Django unit tests all pass (`python manage.py test api`)
- [ ] Comprehensive API tests all pass (`python comprehensive_api_test.py`)
- [ ] Validation script all checks pass (`python validate_setup.py`)

## Troubleshooting

### "LOGBERT_API_KEYS not set"

**Problem**: Environment variable not loaded

**Solution**:
```bash
# Make sure .env file exists
cat .env | grep LOGBERT_API_KEYS

# Load manually
export LOGBERT_API_KEYS="key1,key2,key3"
```

### "No migrations to apply"

**Problem**: Migrations already applied or not created

**Solution**:
```bash
# Force recreation
python manage.py makemigrations api --empty
python manage.py migrate
```

### "Authentication credentials were not provided" (401)

**Problem**: API key not being sent correctly

**Solution**:
```bash
# Check header format - both work:
-H "Authorization: Bearer YOUR_KEY"
-H "X-API-Key: YOUR_KEY"

# Verify API key in .env matches test key
grep LOGBERT_API_KEYS .env
echo $LOGBERT_API_KEY
```

### Tests failing with database errors

**Problem**: Database locked or corrupted

**Solution**:
```bash
# Delete database and recreate
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### "Connection refused" errors

**Problem**: Development server not running

**Solution**:
```bash
# Start server in one terminal
python manage.py runserver

# Run tests in another terminal
python comprehensive_api_test.py
```

### CORS errors in browser

**Problem**: Frontend can't access API

**Solution**:
```python
# In settings.py, add your frontend URL
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # React dev server
    'http://localhost:8000',  # Django dev server
    'http://192.168.1.100:8000',  # Local network
]
```

## Next Steps

After all tests pass:

1. **Review test output** - Make sure you understand what each test does
2. **Check Django admin** - Verify data created by tests appears correctly
3. **Test error cases** - Try invalid data, missing fields, etc.
4. **Performance testing** - Create many records, test pagination
5. **Deploy to PythonAnywhere** - Follow DEPLOYMENT.md
6. **Production testing** - Re-run tests against production URL

## Test Data Cleanup

After testing, you may want to clean up test data:

```bash
# Django shell
python manage.py shell

# Delete test data
from api.models import Alert, SystemMetric, LogStatistic, RawModelOutput
Alert.objects.filter(school_id__startswith='test').delete()
SystemMetric.objects.filter(school_id__startswith='test').delete()
LogStatistic.objects.filter(school_id__startswith='test').delete()
RawModelOutput.objects.filter(school_id__startswith='test').delete()
```

Or simply delete and recreate the database:

```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## Success Criteria

You're ready for production deployment when:

- ✅ All validation checks pass (green)
- ✅ All Django unit tests pass
- ✅ All comprehensive API tests pass (100%)
- ✅ Manual testing confirms data flow works
- ✅ Local pusher successfully sends data
- ✅ Django admin shows all data correctly
- ✅ No errors in server logs
- ✅ Authentication working properly
- ✅ CORS configured correctly

Good luck with your testing! 🚀
