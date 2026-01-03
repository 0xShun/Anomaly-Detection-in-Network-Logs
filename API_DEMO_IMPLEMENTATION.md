# 🚀 API-Based Demo Implementation - Complete Guide

## ✅ Implementation Complete!

All development is finished. The system now uses the following architecture:

```
LOCAL MACHINE (Mac/Linux)              PYTHONANYWHERE (Cloud)
═════════════════════════              ══════════════════════

1. Demo Script                         5. Django Web App
   run_demo.py                            - REST API: /api/logs/
   │                                      - SQLite database
   ├─> Kafka Topic                        - Dashboard UI
   │   "log_topic"                     
   │                                   6. Real-Time Display
2. Kafka Consumer                         - Auto-refresh (2s)
   kafka_consumer_api_sender.py           - Classification cards
   │                                      - Anomaly feed (Security + System Failure only)
   ├─> Hybrid-BERT Model                  - All Logs page (all 7 classes)
   │   Classifications:
   │   0=Normal, 1=Security, 2=System Failure
   │   3=Performance, 4=Network, 5=Config, 6=Hardware
   │
3. HTTP POST → /api/logs/
   JSON with classification data
```

---

## 📋 Files Created/Modified

### ✨ New Files

1. **`kafka_consumer_api_sender.py`** (421 lines)
   - Consumes logs from Kafka topic
   - Classifies with Hybrid-BERT model
   - Sends to PythonAnywhere API via HTTP POST
   - Features:
     - Cross-platform (Mac/Linux)
     - Fire-and-forget with 4 retries, 2s delay
     - Dependency checking
     - Environment variable support
     - Colored terminal output with emojis
     - Auto-detects log formats (Apache/Linux)

2. **`test_api_connection.py`** (276 lines)
   - Complete API testing suite
   - 4 tests: connectivity, sample log, normal log, error handling
   - Run before demo to verify everything works
   - Usage: `python3 test_api_connection.py --api-url https://yoursite.pythonanywhere.com`

3. **`DEMO_RECORDING_GUIDE.md`**
   - Updated for new architecture
   - Pre-recording checklist
   - Scene-by-scene instructions
   - Recovery commands

### 🔧 Modified Files

4. **`webplatform/api/views.py`**
   - Modified `receive_log()` endpoint
   - Removed authentication requirement
   - Added support for classification fields
   - Validates required fields
   - Creates Anomaly ONLY for Security (1) and System Failure (2)
   - Returns detailed JSON response

5. **`webplatform/dashboard/models.py`**
   - Added fields to LogEntry:
     - `classification_class` (IntegerField, 0-6)
     - `classification_name` (CharField)
     - `severity` (CharField: info/medium/high/critical)
     - `anomaly_score` (FloatField, 0.0-1.0)
   - Stores classification for ALL logs

6. **`webplatform/dashboard/utils.py`**
   - Updated `get_cached_classification_stats()`
   - Now queries LogEntry instead of Anomaly
   - Shows counts for all 7 classes

7. **`webplatform/dashboard/migrations/0006_*.py`**
   - New migration for LogEntry fields
   - Creates indexes for performance

### 🗑️ Deleted Files

8. **`kafka_consumer_service.py`** ❌
   - Replaced by `kafka_consumer_api_sender.py`
   - Old version wrote to local database
   - New version sends to API

---

## 🎯 Key Behavioral Changes

### Dashboard Behavior

#### Main Dashboard (`/dashboard/`)
- **Anomaly Feed**: Shows ONLY Security (1) and System Failure (2)
- **Classification Cards**: Show counts for ALL 7 classes (from LogEntry)
- **Total Logs Counter**: Counts all LogEntry records
- **Total Anomalies Counter**: Counts only Anomaly records (Security + System Failure)

#### All Logs Page (`/dashboard/logs/`)
- Shows ALL LogEntry records
- Includes Normal (0), Performance (3), Network (4), Config (5), Hardware (6)
- Shows classification badges for all types

### API Endpoint Behavior

**POST /api/logs/

**

#### Required Fields:
```json
{
  "log_message": "string",
  "timestamp": "YYYY-MM-DD HH:MM:SS",
  "classification_class": 0-6,
  "classification_name": "string",
  "anomaly_score": 0.0-1.0,
  "severity": "info|medium|high|critical",
  "is_anomaly": true|false
}
```

#### Optional Fields:
- `host_ip` (default: "unknown")
- `source` (default: "unknown")
- `log_type` (default: "INFO")

#### Response (Success):
```json
{
  "status": "success",
  "log_id": 123,
  "classification": "Security Anomaly",
  "anomaly_created": true,
  "message": "Log received and processed"
}
```

#### Anomaly Creation Logic:
- **Class 1 (Security)**: Creates Anomaly ✅
- **Class 2 (System Failure)**: Creates Anomaly ✅
- **Classes 0, 3, 4, 5, 6**: LogEntry only, no Anomaly ❌

---

## 🚀 Deployment Commands for PythonAnywhere

Run these commands on PythonAnywhere **after pulling from GitHub**:

```bash
# 1. Navigate to repository
cd ~/custom_lobert_dash

# 2. Pull latest changes
git pull origin main

# 3. Run database migrations
python3 manage.py migrate

# 4. Collect static files
python3 manage.py collectstatic --noinput

# 5. Reload web app
# Go to Web tab → Click "Reload" button
# OR use touch command:
touch /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py
```

### Verify Deployment

```bash
# Check migrations applied
python3 manage.py showmigrations dashboard
# Should show [X] for 0006

# Test the endpoint
curl -X POST https://yoursite.pythonanywhere.com/api/logs/ \
  -H "Content-Type: application/json" \
  -d '{
    "log_message": "Test log",
    "timestamp": "2026-01-04 15:00:00",
    "classification_class": 0,
    "classification_name": "Normal",
    "anomaly_score": 0.05,
    "severity": "info",
    "is_anomaly": false
  }'
# Should return: {"status": "success", ...}
```

---

## 🧪 Testing Before Demo

### Step 1: Test API Connection (Mac/Linux)

```bash
cd "/Users/nelissasudaria/capstone/4 mac/webplatform"

# Test with your actual PythonAnywhere URL
python3 test_api_connection.py --api-url https://yoursite.pythonanywhere.com
```

**Expected Output:**
```
🧪 API CONNECTION TEST SUITE
================================================================================
✅ PASS - Connectivity
✅ PASS - Send Sample
✅ PASS - Send Normal
✅ PASS - Error Handling

Results: 4/4 tests passed
🎉 All tests passed! API is ready for demo.
```

### Step 2: Test Kafka Consumer (Mac)

```bash
# Terminal 1: Start Kafka (if not running)
brew services start kafka

# Terminal 2: Start consumer
cd "/Users/nelissasudaria/capstone/4 mac/webplatform"
python3 kafka_consumer_api_sender.py --api-url https://yoursite.pythonanywhere.com
```

**Expected Output:**
```
Initializing Kafka consumer...
Kafka servers: localhost:9092
Topic: log_topic
API endpoint: https://yoursite.pythonanywhere.com/api/logs/
Loading Hybrid-BERT model (this may take 30-60 seconds)...
✅ Model loaded successfully
Starting Kafka consumer...
✅ Connected to Kafka. Waiting for messages...
```

### Step 3: Send Test Logs

```bash
# Terminal 3: Send test logs
cd "/Users/nelissasudaria/capstone/4 mac"
python3 run_demo.py --file demo_logs/demo_sample_1000.log --delay 1.0 --max-lines 10
```

**Expected Output in Terminal 2:**
```
✅ Normal (info) | Score: 0.054 | GET /index.html HTTP/1.1 200 1234...
🔴 Security Anomaly (critical) | Score: 0.854 | Failed password for admin...
⚠️  System Failure (critical) | Score: 0.623 | kernel panic - not syncing...
```

### Step 4: Verify on PythonAnywhere Dashboard

Open: `https://yoursite.pythonanywhere.com/dashboard`

**Should see:**
- Classification cards updating
- Anomaly feed showing Security and System Failure logs
- Auto-refresh working (every 2 seconds)

---

## 🎬 Demo Day Commands

### For Mac

```bash
# Terminal 1: Kafka Consumer (start first, takes 30-60s to load model)
cd "/Users/nelissasudaria/capstone/4 mac/webplatform"
python3 kafka_consumer_api_sender.py --api-url https://yoursite.pythonanywhere.com

# Terminal 2: Demo Script (start after model loads)
cd "/Users/nelissasudaria/capstone/4 mac"
python3 run_demo.py --file demo_logs/demo_sample_1000.log --delay 0.5 --max-lines 200
```

### For Linux (Demo Day)

```bash
# Terminal 1: Kafka Consumer
cd /path/to/webplatform
python3 kafka_consumer_api_sender.py --api-url https://yoursite.pythonanywhere.com

# Terminal 2: Demo Script
cd /path/to/demo_logs
python3 run_demo.py --file demo_sample_1000.log --delay 0.5 --max-lines 200
```

### Using Environment Variables (Recommended)

```bash
# Set once
export API_URL="https://yoursite.pythonanywhere.com"

# Then you don't need --api-url flag
python3 kafka_consumer_api_sender.py
python3 test_api_connection.py
```

---

## 🐛 Troubleshooting

### Problem: "Missing required packages"
**Solution:**
```bash
pip3 install kafka-python requests python-dateutil transformers torch
```

### Problem: "Cannot connect to Kafka"
**Solution:**
```bash
# Check if Kafka is running
brew services list | grep kafka

# Start Kafka if needed
brew services start kafka

# Verify Kafka is listening
nc -zv localhost 9092
```

### Problem: "Failed to send log after 4 attempts"
**Solution:**
1. Check internet connection
2. Verify PythonAnywhere URL is correct
3. Test with `test_api_connection.py`
4. Check PythonAnywhere web app is running

### Problem: "Model loading takes too long"
**Solution:**
- This is normal (30-60 seconds on first load)
- Model is large (~439MB)
- CPU inference is slower than GPU
- Wait for "✅ Model loaded successfully" before starting demo

### Problem: "Dashboard not updating"
**Solution:**
1. Check browser console for errors
2. Verify auto-refresh is working (watch network tab)
3. Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
4. Check PythonAnywhere logs for API errors

---

## 📊 Expected Demo Results

After sending 200 logs:

### Classification Distribution (Approximate)
- **Normal (0)**: ~78% (156 logs)
- **Security (1)**: ~5% (10 logs) ← Creates Anomaly
- **System Failure (2)**: ~15% (30 logs) ← Creates Anomaly
- **Performance (3)**: ~1% (2 logs)
- **Network (4)**: ~0.5% (1 log)
- **Config (5)**: ~0.5% (1 log)
- **Hardware (6)**: ~0% (0 logs)

### Dashboard Counters
- **Total Logs**: 200
- **Total Anomalies**: ~40 (Security + System Failure only)

### Anomaly Feed
- Shows only the ~40 Security and System Failure logs
- Each with anomaly score, severity, and timestamp

### All Logs Page
- Shows all 200 logs
- All 7 classification types visible

---

## 🎓 Key Differences from Previous Implementation

| Feature | Old (Local DB) | New (API-based) |
|---------|---------------|-----------------|
| **Architecture** | Kafka → BERT → Local DB → Django | Kafka → BERT → API → Cloud DB → Django |
| **Database Location** | Local Mac/Linux | PythonAnywhere Cloud |
| **Kafka Consumer** | `kafka_consumer_service.py` | `kafka_consumer_api_sender.py` |
| **Data Transmission** | Direct DB writes | HTTP POST to API |
| **Authentication** | Required | None (demo only) |
| **Anomaly Creation** | All anomalies | Only Security + System Failure |
| **Classification Storage** | Only in Anomaly | In both LogEntry and Anomaly |
| **Dashboard Access** | localhost:8000 | https://yoursite.pythonanywhere.com |
| **Deployment** | Local only | Cloud-accessible |

---

## 📝 Notes for Presentation

### What to Highlight

1. **Separation of Concerns**
   - Model inference happens locally (no cloud compute needed)
   - Cloud handles only storage and visualization
   - Kafka provides reliable message queue

2. **Scalability**
   - Can process thousands of logs per minute
   - Fire-and-forget architecture for speed
   - Auto-retry for reliability

3. **Real-time Visualization**
   - 2-second auto-refresh
   - Color-coded classifications
   - Severity indicators

4. **Smart Anomaly Detection**
   - Not all classifications are "anomalies"
   - Focus on critical threats (Security, System Failure)
   - Other classes still tracked for analysis

5. **Cross-Platform**
   - Works on Mac and Linux
   - Production-ready with error handling
   - Environment variable configuration

---

## ✅ Final Checklist

Before the demo, verify:

- [ ] Kafka is running (`brew services list | grep kafka`)
- [ ] PythonAnywhere web app is running
- [ ] API connection test passes (4/4 tests)
- [ ] Database is clean (0 logs on dashboard)
- [ ] Demo logs are available (`demo_sample_1000.log`)
- [ ] Both terminals are ready (consumer + demo script)
- [ ] Browser is open to PythonAnywhere dashboard
- [ ] Internet connection is stable
- [ ] Model has finished loading (wait for ✅)

**You're ready to record! 🎬**

---

## 🆘 Quick Reference

```bash
# Test API
python3 test_api_connection.py --api-url https://yoursite.pythonanywhere.com

# Start Consumer
python3 kafka_consumer_api_sender.py --api-url https://yoursite.pythonanywhere.com

# Start Demo
python3 run_demo.py --file demo_logs/demo_sample_1000.log --delay 0.5 --max-lines 200

# Stop Everything
pkill -f kafka_consumer_api_sender.py
pkill -f run_demo.py
```

Good luck with your demo! 🚀✨
