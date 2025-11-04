# Quick Test Reference Card

## 🚀 Fastest Way to Test Everything

```bash
cd /home/shun/Desktop/logbert/webplatform
./quick_setup_test.sh
python manage.py runserver &
export LOGBERT_API_KEY=$(grep LOGBERT_API_KEYS .env | cut -d'=' -f2 | cut -d',' -f1)
export LOGBERT_REMOTE_URL="http://localhost:8000"
python comprehensive_api_test.py
```

## 📋 Test Commands

| Command | What It Does | Expected Result |
|---------|-------------|-----------------|
| `./quick_setup_test.sh` | Complete setup + validation | All checks pass ✅ |
| `python validate_setup.py` | Check configuration | 10/10 checks pass ✅ |
| `python manage.py test api` | Run unit tests | 30+ tests OK ✅ |
| `python comprehensive_api_test.py` | Run API tests | 21+ tests pass ✅ |
| `python manage.py runserver` | Start dev server | Server on :8000 ✅ |

## 🔑 Environment Setup

```bash
# Quick generation of keys
python -c 'import secrets; print(secrets.token_urlsafe(50))'  # SECRET_KEY
python -c 'import secrets; print(secrets.token_urlsafe(32))'  # API_KEY
```

**.env file**:
```env
SECRET_KEY=<50-char-key>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
LOGBERT_API_KEYS=<32-char-key1>,<32-char-key2>
CORS_ALLOWED_ORIGINS=http://localhost:8000
```

## ✅ Pre-Test Checklist

- [ ] `.env` file created with all keys
- [ ] `pip install -r requirements.txt` completed
- [ ] `python manage.py migrate` completed
- [ ] `python manage.py createsuperuser` completed
- [ ] Server running on port 8000
- [ ] `LOGBERT_API_KEY` and `LOGBERT_REMOTE_URL` exported

## 🧪 Test Endpoints Manually

```bash
API_KEY="your-key-here"
BASE="http://localhost:8000"

# Status
curl "$BASE/api/v1/status/" -H "Authorization: Bearer $API_KEY"

# Health
curl -X POST "$BASE/api/v1/health/" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"school_id":"test","status":"healthy"}'

# Create Alert
curl -X POST "$BASE/api/v1/alerts/" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "school_id":"test-001",
    "alert_type":"anomaly",
    "message":"Test alert",
    "level":"high",
    "status":"active"
  }'

# List Alerts
curl "$BASE/api/v1/alerts/" -H "Authorization: Bearer $API_KEY"

# Filter Alerts
curl "$BASE/api/v1/alerts/?level=high" -H "Authorization: Bearer $API_KEY"
```

## 🎯 Success Criteria

| Check | Command | Expected |
|-------|---------|----------|
| Validation | `python validate_setup.py` | 10/10 pass |
| Unit Tests | `python manage.py test api` | All OK |
| API Tests | `python comprehensive_api_test.py` | 100% pass |
| Admin Access | Visit http://localhost:8000/admin | Login works |
| API Status | `curl http://localhost:8000/api/v1/status/` | 200 OK |

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "LOGBERT_API_KEYS not set" | `export LOGBERT_API_KEYS="your-key"` |
| "No migrations" | `python manage.py makemigrations api && python manage.py migrate` |
| "401 Unauthorized" | Check API key matches `.env` file |
| "Connection refused" | Start server: `python manage.py runserver` |
| "Module not found" | `pip install -r requirements.txt` |

## 📁 Test Files

```
webplatform/
├── api/tests.py                    # Unit tests (30+)
├── comprehensive_api_test.py       # API tests (21+)
├── validate_setup.py               # Validation (10 checks)
├── quick_setup_test.sh             # Automated setup
├── TESTING_GUIDE.md                # Full guide
└── TESTING_SUMMARY.md              # This file
```

## 🔢 Test Coverage

- **30+ Unit Tests** - Models, authentication, CRUD
- **21+ API Tests** - End-to-end, integration
- **10+ Validation Checks** - Configuration, setup
- **100% Endpoint Coverage** - All 10 endpoints tested
- **100% Model Coverage** - All 4 models tested
- **100% Auth Coverage** - Valid, invalid, missing keys

## 📊 Expected Output

### Validation ✅
```
Results: 10/10 checks passed
✓ All checks passed!
```

### Unit Tests ✅
```
Ran 30 tests in 5.234s
OK
```

### API Tests ✅
```
Total Tests:  21
Passed:       21
Failed:       0
Pass Rate:    100.0%
✓ ALL TESTS PASSED!
```

## 🎓 Admin Credentials

Default (created by quick_setup_test.sh):
- **Username**: admin
- **Password**: admin123
- **URL**: http://localhost:8000/admin

⚠️ Change in production!

## 🌐 Production Testing

After deploying to PythonAnywhere:

```bash
export LOGBERT_API_KEY="your-production-key"
export LOGBERT_REMOTE_URL="https://yourusername.pythonanywhere.com"
python comprehensive_api_test.py
```

All tests should still pass!

## 📞 Need Help?

1. Check **TESTING_GUIDE.md** for detailed instructions
2. Review **DEPLOYMENT.md** for PythonAnywhere setup
3. Check server logs: `python manage.py runserver --verbosity=2`
4. Run validation: `python validate_setup.py`

---

**Ready to test?** Run: `./quick_setup_test.sh` 🚀
