# 🎬 1-Minute Demo Recording Guide

## Architecture Overview

```
LOCAL MACHINE (Mac/Linux)          CLOUD (PythonAnywhere)
─────────────────────────          ──────────────────────
1. Demo Script                     5. Django Web App
   ↓ (produces logs)                  - REST API endpoint
2. Kafka Topic                        - SQLite database
   ↓ (streams)                        - Dashboard UI
3. Kafka Consumer                  
   ↓ (classifies)                  6. Real-time Display
4. Hybrid-BERT Model                  - Auto-refresh (2s)
   ↓ (sends via API)                  - Classification cards
   → HTTPS POST → /api/logs/          - Anomaly feed
```

## Pre-Recording Checklist

### 1. Test API Connection (IMPORTANT!)
```bash
cd "/Users/nelissasudaria/capstone/4 mac"
python3 test_api_connection.py --api-url https://yoursite.pythonanywhere.com
```
**Expected output:** All 4 tests should pass ✅

### 2. Verify Kafka is Running
```bash
brew services list | grep kafka
# Should show: kafka started
```

### 3. Set Environment Variable (Optional)
```bash
export API_URL="https://yoursite.pythonanywhere.com"
# This way you don't need --api-url flag
```

### 4. Verify Database is Clean on PythonAnywhere
Go to: https://yoursite.pythonanywhere.com/dashboard
- Should show all cards at 0
- Anomaly feed should be empty

---

## Recording Steps (1 Minute)

### Scene 1: Empty Dashboard (0:00-0:10)
**What to show:**
- Clean dashboard with 7 classification cards all showing "0"
- Empty anomaly feed table
- Red "Disconnected" badge
- Point to "Refresh" button

**Narration:**
> "Starting with an empty dashboard monitoring real-time log anomalies using Hybrid-BERT from Hugging Face."

---

## Recording Steps (1 Minute)

### Scene 1: Empty Dashboard (0:00-0:10)
**What to show:**
- Open: https://yoursite.pythonanywhere.com/dashboard
- Clean dashboard with 7 classification cards all showing "0"
- Empty anomaly feed table
- Point to "Refresh" button

**Narration:**
> "Starting with an empty cloud dashboard monitoring real-time log anomalies using Hybrid-BERT from Hugging Face."

---

### Scene 2: Start Services (0:10-0:20)
**Terminal Commands:**

**Terminal 1** (Start Kafka Consumer - sends to API):
```bash
cd "/Users/nelissasudaria/capstone/4 mac"
python3 kafka_consumer_api_sender.py --api-url https://yoursite.pythonanywhere.com
```

**Terminal 2** (Start Demo - Visible on screen):
```bash
cd "/Users/nelissasudaria/capstone/4 mac"
python3 run_demo.py --file demo_logs/demo_sample_1000.log --delay 0.5 --max-lines 200
```

**What to show:**
- Terminal 1: Model loading message (30-60s)
- Terminal 2: Logs streaming to Kafka
- Browser: Dashboard starting to update
- First few logs appear on PythonAnywhere dashboard

**Narration:**
> "We start streaming 200 production logs through Kafka. The local Hybrid-BERT model classifies each log and sends results to our cloud dashboard via API."

---

### Scene 3: Real-Time Updates (0:20-0:45)
**What to show:**
- PythonAnywhere dashboard auto-refreshing every 2 seconds
- Counter increasing: 10 → 50 → 100 → 150+
- Classification cards updating:
  - Normal (green) increasing fastest
  - Security Anomaly (red) appearing (only these create Anomaly records)
  - System Failure (dark red) showing up (only these create Anomaly records)
  - Other classes (Performance, Network, Config, Hardware) visible in "All Logs" page
- Anomaly feed showing only Security and System Failure logs
- Terminal showing classifications with emojis (✅ Normal, 🔴 Security, ⚠️ System Failure)

**Important Note:**
- Main dashboard shows ONLY Security (class 1) and System Failure (class 2) anomalies
- All 7 classifications visible on classification cards (counts from ALL logs)
- Visit `/dashboard/logs/` to see all log types including Normal, Performance, Network, Config, Hardware

**Narration:**
> "Watch as logs are classified into 7 categories. The dashboard highlights critical threats - Security anomalies and System failures - while tracking all log types."

**Visual Focus:**
- Split screen: Terminal (left) + Dashboard (right)
- Or: Full dashboard with stats/table visible

---

### Scene 4: Interactive Features (0:45-0:55)
**What to show:**
- Click the "Refresh" button manually
- Hover over a log message to see full text
- Point to key columns:
  - Anomaly Score (e.g., 0.769)
  - Classification (Security Anomaly)
  - Severity (Critical)
- Show IP addresses being parsed
- Show timestamps formatted properly

**Narration:**
> "The dashboard offers real-time insights with anomaly scores, severity indicators, and detailed log information."

---

### Scene 5: Final Results (0:55-1:00)
**What to show:**
- Final statistics visible on classification cards
- Example: "Normal: 156, Security: 12, System Failure: 30, Hardware: 2"
- Quick glance at the populated anomaly feed
- End frame or fade to text: "Powered by Hybrid-BERT (Hugging Face)"

**Narration:**
> "In seconds, we've processed 200 logs with AI-powered classification, ready for security teams to investigate."

---

## Camera/Screen Recording Tips

### Option A: Full Screen Dashboard (Recommended)
- Record browser at **1920x1080** or **1280x720**
- Use browser zoom at **100%** or **110%** for visibility
- Hide bookmarks bar for clean look

### Option B: Split Screen
- Left: Terminal (40%) showing demo script output
- Right: Browser (60%) showing dashboard
- Use tmux or iTerm2 split panes

### Recommended Tools:
- **macOS**: QuickTime Screen Recording (free)
- **Professional**: OBS Studio (free, open-source)
- **Quick/Easy**: Loom (free tier available)

---

## Pre-Flight Check (Run 1 minute before recording)

### 1. Ensure Kafka is Running
```bash
brew services list | grep kafka
# Should show: kafka started
```

### 2. Verify Django is Running
```bash
curl http://localhost:8000/dashboard/ -I
# Should return: HTTP/1.1 200 OK
```

### 3. Test Database is at Zero
```bash
python3 check_stats.py
```

### 4. Test Demo Script (Dry Run)
```bash
# Send just 5 logs to test
python3 run_demo.py --file demo_logs/demo_sample_1000.log --delay 1.0 --max-lines 5
```

Then reset database again before actual recording.

---

## Recovery Commands (If Something Goes Wrong)

### Stop All Services
```bash
# Stop Kafka consumer
pkill -f kafka_consumer_api_sender.py

# Stop demo script
pkill -f run_demo.py
```

### Clear Database on PythonAnywhere
Login to PythonAnywhere console and run:
```bash
cd ~/custom_lobert_dash
python3 manage.py shell
```
```python
from dashboard.models import LogEntry, Anomaly
Anomaly.objects.all().delete()
LogEntry.objects.all().delete()
exit()
```

### Restart Clean
```bash
# Restart consumer (will take 30-60s to load model)
python3 kafka_consumer_api_sender.py --api-url https://yoursite.pythonanywhere.com &

# Wait for model to load, then restart demo
python3 run_demo.py --file demo_logs/demo_sample_1000.log --delay 0.5 --max-lines 200
```

---

## Post-Recording

### Stop Services
```bash
# Stop consumer
pkill -f kafka_consumer_service.py

# Keep Django running for later use
```

### Video Editing Tips
- Add title card: "Real-Time Log Anomaly Detection with Hybrid-BERT"
- Add text overlays for key features
- Speed up 2x if needed to fit exactly 60 seconds
- Add background music (optional, keep it subtle)
- Export at 1080p, 30fps

---

## Alternative: Pre-Recorded Terminal Commands

If you want smoother terminal appearance, create this script:

```bash
#!/bin/bash
# demo_record.sh

echo "🚀 Starting Kafka Consumer..."
python3 kafka_consumer_service.py > /tmp/consumer.log 2>&1 &
sleep 2

echo "📊 Streaming logs to Hybrid-BERT model..."
python3 run_demo.py --file demo_logs/demo_sample_1000.log --delay 0.5 --max-lines 200
```

Make executable:
```bash
chmod +x demo_record.sh
```

Then just run `./demo_record.sh` during recording.

---

## Expected Results

By end of 1-minute demo:
- **~200 logs processed**
- **Distribution**: ~78% Normal, ~15% System Failure, ~5% Security, ~2% Others
- **Dashboard**: Fully populated with live data
- **Impression**: Fast, accurate, real-time AI-powered monitoring

Good luck with your recording! 🎥✨
