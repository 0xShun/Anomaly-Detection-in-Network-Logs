# Quick Demo Guide - Local Testing

## 🚀 Quick Start (5 Minutes)

### Step 1: Set API Keys
```bash
export LOGBERT_API_KEYS="a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4,r-rFoV_GY_DZAKe7JItNpXI59UX2TsrwK12LSgAYx_Q,Wm-SMUc90uqCUi94GvD1dZ_pcSyIF4G-sGrtCCc06Ww"
```

### Step 2: Start Server
```bash
cd webplatform
python3 manage.py runserver
```

### Step 3: Open Dashboard in Browser
```
http://localhost:8000/dashboard/
```
Login: `admin` / `admin123`

---

## 📊 Demo Scenario 1: Send Logs via API

### Open a new terminal and send test logs:

#### 1. Security Anomaly (Creates Anomaly Alert)
```bash
curl -X POST http://localhost:8000/api/v1/logs/ \
  -H "X-API-Key: a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4" \
  -H "Content-Type: application/json" \
  -d '{
    "log_message": "Failed password for admin from 192.168.1.100",
    "timestamp": "2026-01-04 15:30:00",
    "classification_class": 1,
    "classification_name": "Security Anomaly",
    "anomaly_score": 0.92,
    "severity": "critical",
    "is_anomaly": true
  }'
```

#### 2. System Failure (Creates Anomaly Alert)
```bash
curl -X POST http://localhost:8000/api/v1/logs/ \
  -H "X-API-Key: a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4" \
  -H "Content-Type: application/json" \
  -d '{
    "log_message": "Kernel panic - not syncing",
    "timestamp": "2026-01-04 15:31:00",
    "classification_class": 2,
    "classification_name": "System Failure",
    "anomaly_score": 0.88,
    "severity": "critical",
    "is_anomaly": true
  }'
```

#### 3. Normal Log (No Anomaly)
```bash
curl -X POST http://localhost:8000/api/v1/logs/ \
  -H "X-API-Key: a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4" \
  -H "Content-Type: application/json" \
  -d '{
    "log_message": "GET /index.html HTTP/1.1 200",
    "timestamp": "2026-01-04 15:32:00",
    "classification_class": 0,
    "classification_name": "Normal",
    "anomaly_score": 0.05,
    "severity": "info",
    "is_anomaly": false
  }'
```

#### 4. Performance Issue (No Anomaly)
```bash
curl -X POST http://localhost:8000/api/v1/logs/ \
  -H "X-API-Key: a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4" \
  -H "Content-Type: application/json" \
  -d '{
    "log_message": "High CPU usage: 95%",
    "timestamp": "2026-01-04 15:33:00",
    "classification_class": 3,
    "classification_name": "Performance Issue",
    "anomaly_score": 0.65,
    "severity": "medium",
    "is_anomaly": false
  }'
```

---

## 🎯 Demo Scenario 2: Automated Testing

Run all tests automatically:
```bash
python3 run_local_tests.py
```

This will:
- ✅ Start Django server
- ✅ Run 10 comprehensive tests
- ✅ Create sample logs (all 7 classifications)
- ✅ Stop server automatically

---

## 📈 What to Show in Demo

### 1. Dashboard (`http://localhost:8000/dashboard/`)
- **Total Logs Count** - Shows all received logs
- **Active Anomalies** - Only Security (Class 1) and System Failure (Class 2)
- **Classification Distribution** - Pie chart with all 7 types
- **Recent Logs Table** - Shows latest logs with severity colors

### 2. Analytics Page (`http://localhost:8000/analytics/`)
- **Log Volume Over Time** - Stacked bar chart by minute
  - Shows all 7 classifications color-coded
  - Real-time updates with "Refresh Charts" button
- **Classification Distribution** - Pie chart
  - 7 classifications: Normal, Security, System Failure, Performance, Network, Configuration, Data

### 3. Anomaly Logic Demonstration
**Key Point:** Only Classes 1 & 2 create anomaly records
- ✅ Class 0 (Normal) → Log created, no anomaly
- ✅ Class 1 (Security) → Log + Anomaly created
- ✅ Class 2 (System Failure) → Log + Anomaly created
- ✅ Class 3 (Performance) → Log created, no anomaly
- ✅ Class 4 (Network) → Log created, no anomaly
- ✅ Class 5 (Configuration) → Log created, no anomaly
- ✅ Class 6 (Data) → Log created, no anomaly

---

## 🔧 Quick Commands

### Reset Database (Start Fresh)
```bash
python3 manage.py shell
```
```python
from dashboard.models import LogEntry, Anomaly
Anomaly.objects.all().delete()
LogEntry.objects.all().delete()
print("Database cleared")
exit()
```

### Check Logs in Database
```bash
python3 manage.py shell
```
```python
from dashboard.models import LogEntry
print(f"Total logs: {LogEntry.objects.count()}")
for log in LogEntry.objects.all()[:5]:
    print(f"{log.timestamp} - Class {log.classification_class}: {log.classification_name}")
exit()
```

### Send Multiple Logs Quickly
```bash
# Copy this entire block and paste in terminal
for i in {1..10}; do
  curl -s -X POST http://localhost:8000/api/v1/logs/ \
    -H "X-API-Key: a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4" \
    -H "Content-Type: application/json" \
    -d "{
      \"log_message\": \"Test log $i\",
      \"timestamp\": \"2026-01-04 15:00:$i\",
      \"classification_class\": $((i % 7)),
      \"classification_name\": \"Test\",
      \"anomaly_score\": 0.5,
      \"severity\": \"info\",
      \"is_anomaly\": false
    }" && echo "Log $i sent"
done
```

---

## 🎬 Demo Script

### Introduction (30 seconds)
"This is a real-time log anomaly detection dashboard using Hybrid-BERT classification with 7 different log types."

### Step 1: Show Empty Dashboard (10 seconds)
- Open `http://localhost:8000/dashboard/`
- Point out: Total Logs: 0, Active Anomalies: 0

### Step 2: Send Security Anomaly (20 seconds)
- Run curl command for Security Anomaly
- Refresh dashboard
- Show: Anomaly count increased, log appears in table

### Step 3: Send Normal Log (20 seconds)
- Run curl command for Normal log
- Refresh dashboard
- Show: Log count increased, but no new anomaly (only Security/System Failure create anomalies)

### Step 4: Show Analytics (30 seconds)
- Navigate to `http://localhost:8000/analytics/`
- Show Log Volume chart with stacked classifications
- Show Classification Distribution pie chart
- Click "Refresh Charts" to demonstrate real-time updates

### Step 5: Send Multiple Logs (30 seconds)
- Run the loop command to send 10 logs
- Refresh analytics page
- Show updated charts with all classifications

### Conclusion (20 seconds)
"The system successfully classifies logs into 7 types, creates anomaly alerts only for critical issues (Security and System Failures), and provides real-time analytics for monitoring."

**Total Demo Time: ~2.5 minutes**

---

## 🐛 Troubleshooting

### Port 8000 already in use
```bash
pkill -f "manage.py runserver"
python3 manage.py runserver
```

### API returns 403 error
Make sure you set the API key environment variable:
```bash
export LOGBERT_API_KEYS="a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4"
```

### Charts not updating
1. Click "Refresh Charts" button
2. Or refresh the page (F5)

### Database locked error
```bash
pkill -f "manage.py runserver"
sleep 2
python3 manage.py runserver
```

---

## 📝 Notes for Demo

- **7 Classification Types:**
  - 0: Normal
  - 1: Security Anomaly
  - 2: System Failure
  - 3: Performance Issue
  - 4: Network Anomaly
  - 5: Configuration Issue
  - 6: Data Anomaly

- **Anomaly Creation Logic:**
  - Only Class 1 (Security) and Class 2 (System Failure) create anomaly records
  - All other classes are logged but not flagged as anomalies
  - This prevents alert fatigue while tracking all log types

- **Analytics Features:**
  - Minute-based grouping for real-time monitoring
  - Color-coded stacked bars for easy visualization
  - Pie chart shows distribution across all 7 types
  - Auto-refresh capability

---

**Ready to Demo! 🚀**
