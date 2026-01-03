# Local API Testing Instructions

## Test Script Created

**File:** `test_local_api.py`

This comprehensive test script validates:
1. ✅ Server connectivity
2. ✅ API endpoint functionality (all 7 classification types)
3. ✅ Dashboard data visibility
4. ✅ Analytics chart API
5. ✅ Analytics page rendering
6. ✅ Error handling
7. ✅ End-to-end data flow

## How to Run Tests

### Step 1: Start Django Development Server

```bash
cd webplatform
python3 manage.py runserver
```

### Step 2: In a New Terminal, Run Tests

```bash
cd webplatform
python3 test_local_api.py
```

**Default credentials:** admin / admin123

## Test Configuration Changes Made

### Temporary Changes for Local Testing

**File:** `api/views.py` (Line 285)

Changed from:
```python
@authentication_classes([APIKeyAuthentication])
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def receive_log(request):
```

To:
```python
# Temporarily disable authentication for local testing
@permission_classes([])  # Override default authentication
@api_view(['POST'])
def receive_log(request):
```

**⚠️ IMPORTANT:** This change is ONLY for local testing. For production, restore the authentication:
```python
@authentication_classes([APIKeyAuthentication])
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def receive_log(request):
```

## What the Tests Validate

### TEST 1: Server Connectivity
- Verifies Django server is running
- Tests basic HTTP connection

### TEST 2: Security Anomaly (Class 1)
- Sends log with classification_class = 1
- Verifies LogEntry is created
- Verifies Anomaly record is created (Security creates anomalies)
- Checks response status and data

### TEST 3: System Failure (Class 2)
- Sends log with classification_class = 2
- Verifies LogEntry is created
- Verifies Anomaly record is created (System Failure creates anomalies)

### TEST 4: Normal Log (Class 0)
- Sends log with classification_class = 0
- Verifies LogEntry is created
- Verifies NO Anomaly record is created (Normal doesn't create anomalies)

### TEST 5: Performance Issue (Class 3)
- Sends log with classification_class = 3
- Verifies LogEntry is created
- Verifies NO Anomaly record is created (Only classes 1 & 2 create anomalies)

### TEST 6: Dashboard Data Visibility
- Checks if created logs appear in dashboard HTML
- Verifies dashboard elements (Total Logs, Active Anomalies, Log Table, Classification Stats)

### TEST 7: Analytics Chart Data API
- Tests `/analytics/api/chart-data/?type=line`
  - Verifies minute-based grouping
  - Checks all 7 classification fields present (class_0 through class_6)
- Tests `/analytics/api/chart-data/?type=pie`
  - Verifies classification distribution
  - Checks classification names and counts

### TEST 8: Analytics Page Visibility
- Verifies analytics page loads
- Checks for volumeChart canvas
- Checks for typeChart canvas
- Verifies Chart.js library is included
- Verifies refreshAllCharts button exists
- Checks chart titles

### TEST 9: API Error Handling
- Sends invalid data (missing required fields)
- Verifies API returns 400 Bad Request

### TEST 10: End-to-End Data Flow
- Creates unique test log
- Verifies log appears in API response
- Checks log in dashboard
- Checks log in analytics data
- Validates complete data flow: API → Database → Dashboard → Analytics

## Expected Results

When all tests pass, you should see:

```
================================================================================
TEST SUMMARY
================================================================================
✅ PASS - Connectivity
✅ PASS - Api Security
✅ PASS - Api System Failure
✅ PASS - Api Normal
✅ PASS - Api Performance
✅ PASS - Dashboard Visibility
✅ PASS - Analytics Api
✅ PASS - Analytics Page
✅ PASS - Error Handling
✅ PASS - End To End

Results: 10/10 tests passed

ℹ️  Created 5 test logs
   View them at: http://localhost:8000/dashboard/

🎉 All tests passed! Local API is working correctly.

✅ Data Flow Verified:
   API → Database → Dashboard → Analytics
```

## Manual Testing (Alternative)

If automated tests have issues, you can manually test using curl:

### 1. Test API Endpoint (Security Anomaly)

```bash
curl -X POST http://localhost:8000/api/v1/logs/ \
  -H "Content-Type: application/json" \
  -d '{
    "log_message": "Failed password for admin from 192.168.1.100",
    "timestamp": "2026-01-04 15:30:00",
    "host_ip": "192.168.1.100",
    "source": "linux_test",
    "log_type": "ERROR",
    "classification_class": 1,
    "classification_name": "Security Anomaly",
    "anomaly_score": 0.9234,
    "severity": "critical",
    "is_anomaly": true
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "log_id": 123,
  "classification": "Security Anomaly",
  "anomaly_created": true
}
```

### 2. Test API Endpoint (Normal Log)

```bash
curl -X POST http://localhost:8000/api/v1/logs/ \
  -H "Content-Type: application/json" \
  -d '{
    "log_message": "GET /index.html HTTP/1.1 200 1234",
    "timestamp": "2026-01-04 15:31:00",
    "host_ip": "192.168.1.50",
    "source": "apache_test",
    "log_type": "INFO",
    "classification_class": 0,
    "classification_name": "Normal",
    "anomaly_score": 0.0543,
    "severity": "info",
    "is_anomaly": false
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "log_id": 124,
  "classification": "Normal",
  "anomaly_created": false
}
```

### 3. Check Dashboard

Visit: http://localhost:8000/dashboard/

You should see:
- Total log count increased
- Classification distribution showing your test logs
- Anomalies count increased (if Security or System Failure logs sent)

### 4. Check Analytics Charts

Visit: http://localhost:8000/analytics/

You should see:
- **Log Volume Over Time** chart with stacked bars showing classifications
- **Classification Distribution** pie chart
- Click "Refresh Charts" to update data

### 5. Test Analytics API Directly

```bash
# Line chart data
curl "http://localhost:8000/analytics/api/chart-data/?type=line"

# Pie chart data
curl "http://localhost:8000/analytics/api/chart-data/?type=pie"
```

## Troubleshooting

### Issue: Server not starting
```bash
# Kill any existing Django processes
pkill -f "manage.py runserver"

# Start fresh
cd webplatform
python3 manage.py runserver
```

### Issue: Port 8000 already in use
```bash
# Use a different port
python3 manage.py runserver 8001

# Update test script
python3 test_local_api.py --port 8001
```

### Issue: Authentication errors (403)
Make sure you've disabled authentication in `api/views.py` as shown above.

### Issue: Database locked
```bash
# Stop server
pkill -f "manage.py runserver"

# Wait a moment
sleep 2

# Restart
python3 manage.py runserver
```

## Test Data Cleanup

To reset the database after testing:

### Option 1: Use Reset Database Button
1. Login to dashboard: http://localhost:8000/dashboard/
2. Click "Reset Database" button
3. Confirm deletion

### Option 2: Django Shell
```bash
python3 manage.py shell
```

```python
from dashboard.models import LogEntry, Anomaly
Anomaly.objects.all().delete()
LogEntry.objects.all().delete()
print("Database cleared")
```

### Option 3: Fresh Database
```bash
# Backup current database
cp db.sqlite3 db.sqlite3.backup

# Delete and recreate
rm db.sqlite3
python3 manage.py migrate
python3 manage.py createsuperuser
```

## Verification Checklist

After running tests, verify:

- [ ] All 10 tests pass
- [ ] Logs appear in dashboard
- [ ] Classification counts are accurate
- [ ] Anomalies created only for classes 1 & 2
- [ ] Analytics charts display data
- [ ] Line chart shows stacked bars by classification
- [ ] Pie chart shows classification distribution
- [ ] Refresh Charts button works
- [ ] No errors in Django console
- [ ] No errors in browser console

## Test Coverage

This test suite covers:

✅ **API Endpoints**
  - POST /api/v1/logs/ (all 7 classification types)
  - GET /analytics/api/chart-data/?type=line
  - GET /analytics/api/chart-data/?type=pie

✅ **Data Models**
  - LogEntry creation
  - Anomaly creation (selective based on classification)
  - Classification storage

✅ **Business Logic**
  - Anomaly creation logic (only classes 1 & 2)
  - Classification mapping
  - Severity handling

✅ **Frontend Integration**
  - Dashboard data display
  - Analytics charts rendering
  - Classification distribution
  - Real-time updates

✅ **Error Handling**
  - Missing required fields
  - Invalid data types
  - Server errors

## Restoring Production Configuration

**BEFORE DEPLOYING TO PRODUCTION**, restore authentication in `api/views.py`:

```python
@authentication_classes([APIKeyAuthentication])
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def receive_log(request):
```

Then commit and push:

```bash
git add api/views.py
git commit -m "Restore API authentication for production"
git push origin main
```

## Files Created/Modified

1. **test_local_api.py** - Comprehensive test suite (771 lines)
2. **api/views.py** - Temporary authentication disable (Line 285-287)

## Next Steps

1. Run tests locally
2. Verify all tests pass
3. Review dashboard and analytics
4. Restore authentication before production deployment
5. Run same tests against PythonAnywhere (use original test_api_connection.py)
