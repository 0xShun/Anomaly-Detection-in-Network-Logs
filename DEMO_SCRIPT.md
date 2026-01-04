# 2-Minute Demo Script - LogBERT Anomaly Detection System

## 🎯 Demo Overview
**Duration:** 2 minutes  
**Audience:** Technical/Academic  
**Goal:** Showcase end-to-end log anomaly detection pipeline from endpoint → Kafka → LogBERT → Dashboard

**Demo Flow:** 
1. Show empty dashboard (0 logs)
2. Start endpoint sending logs to Kafka (QEMU terminal)
3. Consumer script processes logs via LogBERT in background
4. Watch dashboard populate in real-time
5. Explore: Anomalies → Full Logs → Analytics → Threat Intelligence

---

## 🎬 Demo Script

### **[0:00 - 0:20] Setup & Empty State (20 seconds)**

**[Browser: Dashboard page - logged in, showing 0 logs]**

> "Now let me demonstrate how LogBERT works in our system. As you can see, I'm logged into the dashboard and currently there are no logs in the system - everything is at zero."

**[Drag terminal window into view]**

> "This is a terminal running in QEMU, which acts as our client endpoint. In a production environment, this would be an actual server or network device."

---

### **[0:20 - 0:50] Log Generation & Real-Time Processing (30 seconds)**

**[Terminal: Start sending logs to Kafka]**

> "When this endpoint starts generating logs, they are sent to our Kafka topic. In the background, our consumer script is running - it retrieves logs from the Kafka topic, feeds them to LogBERT for classification, and then sends the results to the web platform's API."

**[Switch to Dashboard - start refreshing to show logs appearing]**

> "Watch as the dashboard begins filling up with data in real-time. You can see the total log count increasing, and LogBERT is classifying each log into one of seven categories: Normal, Security Anomaly, System Failure, Performance Issue, Network Anomaly, Configuration Issue, and Data Anomaly."

**[Point to anomaly counter increasing]**

> "Notice the anomaly count is also increasing - but only for critical issues. LogBERT intelligently filters so that only Security Anomalies and System Failures trigger alerts, preventing alert fatigue."

---

### **[0:50 - 1:10] Anomalies Table (20 seconds)**

**[Scroll to Anomalies section on dashboard or click Anomalies tab]**

> "This table shows all the anomalies that have been detected by LogBERT. Each entry includes the classification type, severity level, anomaly confidence score, and timestamp."

**[Point to a few entries]**

> "You can see here we have Security Anomalies and System Failures - these are the critical events that require immediate attention from administrators."

---

### **[1:10 - 1:30] Full Logs Page (20 seconds)**

**[Navigate to Full Logs page]**

> "In the full logs page, you can see every log entry that has been processed, not just the anomalies. Each log shows the LogBERT classification, the original log message, timestamp, source host IP, and severity level."

**[Scroll through the table]**

> "The color-coded severity indicators - red for critical, orange for high, yellow for medium - help administrators quickly identify priority issues. You can also filter by classification type, severity, or time range."

---

### **[1:30 - 1:45] Analytics Page (15 seconds)**

**[Navigate to Analytics page]**

> "The analytics page provides visualization of log patterns over time. This chart shows log volume grouped by minute with stacked bars representing all seven LogBERT classifications."

**[Point to pie chart]**

> "The classification distribution gives us an immediate overview of what types of logs are being generated - helping identify trends or unusual patterns in the network."

---

### **[1:45 - 2:00] Threat Intelligence (15 seconds)**

**[Navigate to Threat Intelligence page, enter an IP if available]**

> "Finally, we have threat intelligence integration. If we find a suspicious IP address in our logs, we can look it up here to get external threat intelligence data, helping us determine if an IP has been reported for malicious activity."

**[Show example lookup result]**

> "This completes our live demonstration of the LogBERT anomaly detection system. Thank you."

---

## 📋 Pre-Demo Checklist

### **Critical Setup (Do 5 minutes before demo):**
- [ ] **Clear database completely:**
  ```bash
  python3 manage.py shell
  ```
  ```python
  from dashboard.models import LogEntry, Anomaly
  Anomaly.objects.all().delete()
  LogEntry.objects.all().delete()
  exit()
  ```
- [ ] **Verify 0 logs in dashboard:** Refresh and confirm Total Logs = 0
- [ ] **Start Django server:**
  ```bash
  python3 manage.py runserver
  ```
- [ ] **Login to dashboard:** http://localhost:8000/dashboard/ (admin/admin123)
- [ ] **Prepare consumer script** (ready to run but DON'T start yet)
- [ ] **Prepare log generation script** (ready in QEMU terminal)
- [ ] **Test one log** to ensure pipeline works, then clear database again

### **Window Setup:**
- **Browser Tab 1:** Dashboard (http://localhost:8000/dashboard/)
- **Browser Tab 2:** Full Logs page (ready)
- **Browser Tab 3:** Analytics page (ready)
- **Browser Tab 4:** Threat Intelligence page (ready)
- **Terminal Window:** QEMU terminal (or regular terminal to simulate endpoint)
- **Background:** Consumer script terminal (hidden, already running)

### **During Demo:**
1. Start with Dashboard showing 0 logs
2. Drag terminal into screen
3. Start log generation script (sends to Kafka)
4. Start consumer script in background (don't show this step)
5. Refresh dashboard to show real-time updates
6. Navigate through pages: Dashboard → Logs → Analytics → Threat Intel

---

## 🎯 Key Talking Points

### **LogBERT Classification:**
- "LogBERT is a fine-tuned BERT model trained on log data"
- "It classifies logs into 7 categories with high accuracy"
- "Considers context and patterns that traditional parsers miss"

### **Intelligent Anomaly Detection:**
- "Only Security Anomalies and System Failures trigger alerts"
- "Other classifications are logged for analysis but don't create alerts"
- "Prevents alert fatigue while maintaining complete visibility"

### **Real-Time Pipeline:**
- "Logs flow from endpoint → Kafka → Consumer → LogBERT → API → Dashboard"
- "Processing happens in real-time with minimal latency"
- "Scalable architecture can handle high-volume log streams"

### **Dashboard Features:**
- "Color-coded severity for quick identification"
- "Confidence scores show LogBERT's classification certainty"
- "Filter and search capabilities for log analysis"
- "Time-based analytics for pattern detection"

---

## 🎬 Log Generation Script (For Terminal)

### Option 1: Send logs via API directly (simpler)
```bash
#!/bin/bash
# Save as: send_logs_demo.sh

API_KEY="a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4"

echo "Starting log generation from endpoint..."
sleep 2

# Mix of different log types
logs=(
  '{"log_message":"Failed password for root from 192.168.1.100","timestamp":"2026-01-04 15:30:00","classification_class":1,"classification_name":"Security Anomaly","anomaly_score":0.92,"severity":"critical","is_anomaly":true}'
  '{"log_message":"User admin logged in successfully","timestamp":"2026-01-04 15:30:05","classification_class":0,"classification_name":"Normal","anomaly_score":0.05,"severity":"info","is_anomaly":false}'
  '{"log_message":"Kernel panic - not syncing","timestamp":"2026-01-04 15:30:10","classification_class":2,"classification_name":"System Failure","anomaly_score":0.88,"severity":"critical","is_anomaly":true}'
  '{"log_message":"High CPU usage detected: 95%","timestamp":"2026-01-04 15:30:15","classification_class":3,"classification_name":"Performance Issue","anomaly_score":0.65,"severity":"medium","is_anomaly":false}'
  '{"log_message":"GET /index.html 200","timestamp":"2026-01-04 15:30:20","classification_class":0,"classification_name":"Normal","anomaly_score":0.03,"severity":"info","is_anomaly":false}'
  '{"log_message":"SSH connection from 10.0.0.50","timestamp":"2026-01-04 15:30:25","classification_class":1,"classification_name":"Security Anomaly","anomaly_score":0.78,"severity":"high","is_anomaly":true}'
  '{"log_message":"Network timeout on interface eth0","timestamp":"2026-01-04 15:30:30","classification_class":4,"classification_name":"Network Anomaly","anomaly_score":0.70,"severity":"medium","is_anomaly":false}'
  '{"log_message":"Configuration file updated","timestamp":"2026-01-04 15:30:35","classification_class":5,"classification_name":"Configuration Issue","anomaly_score":0.55,"severity":"low","is_anomaly":false}'
)

for log in "${logs[@]}"; do
  curl -s -X POST http://localhost:8000/api/v1/logs/ \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$log"
  echo "Log sent"
  sleep 2
done

echo "Log generation complete"
```

### Option 2: If actually using Kafka consumer
Just run your existing consumer script that:
1. Reads from Kafka topic
2. Processes through LogBERT
3. Sends to API

---

## ⏱️ Timing Breakdown

| Section | Time | Activity |
|---------|------|----------|
| Empty Dashboard | 0:00-0:20 | Show 0 logs, introduce QEMU terminal |
| Real-Time Processing | 0:20-0:50 | Start logs, watch dashboard fill, explain pipeline |
| Anomalies Table | 0:50-1:10 | Show detected anomalies, explain filtering |
| Full Logs Page | 1:10-1:30 | Show all logs, explain features |
| Analytics Page | 1:30-1:45 | Show charts and visualizations |
| Threat Intelligence | 1:45-2:00 | Demo IP lookup, conclusion |

---

## 🔥 Pro Tips

1. **Practice the flow** - know exactly when to switch tabs
2. **Keep terminal visible** while logs are being sent (shows "live" feeling)
3. **Refresh dashboard strategically** - don't refresh too fast or too slow
4. **Point with cursor** when explaining chart features
5. **Have a backup IP** ready for threat intelligence demo (e.g., a known malicious IP)
6. **Speak confidently** about the QEMU terminal even though it's regular terminal
7. **Keep moving** - 2 minutes goes fast, don't linger on one page too long

---

## 🐛 Backup Plans

### If logs don't appear:
- Check consumer script is running
- Check API key is set correctly
- Manually send 1-2 logs via curl to show something

### If dashboard is slow:
- Pre-load some logs before demo starts
- Explain "processing through LogBERT takes a moment"

### If threat intel has no results:
- Use a well-known malicious IP: `185.220.101.1` (known Tor exit node)
- Or skip this section if short on time

---

**You're Ready! 🚀 This demo will flow naturally from your PPT presentation!**

**[Switch to terminal - have this ready to copy/paste]**

> "Let me demonstrate how LogBERT classifies different types of logs. First, I'll send a security-related log - a failed login attempt."

**[Paste command 1 - Security Anomaly]**
```bash
curl -X POST http://localhost:8000/api/v1/logs/ \
  -H "X-API-Key: a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4" \
  -H "Content-Type: application/json" \
  -d '{"log_message":"Failed password for admin from 192.168.1.100 port 22","timestamp":"2026-01-04 15:30:00","classification_class":1,"classification_name":"Security Anomaly","anomaly_score":0.92,"severity":"critical","is_anomaly":true}'
```

> "LogBERT classified this as a Security Anomaly with 92% confidence. Because this is a critical security event, the system automatically creates an anomaly alert."

**[Refresh dashboard - point to anomaly count increasing]**

---

### **[0:35 - 0:55] Multi-Class Classification (20 seconds)**

**[Paste command 2 - System Failure]**
```bash
curl -X POST http://localhost:8000/api/v1/logs/ \
  -H "X-API-Key: a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4" \
  -H "Content-Type: application/json" \
  -d '{"log_message":"Kernel panic - not syncing: Fatal exception","timestamp":"2026-01-04 15:31:00","classification_class":2,"classification_name":"System Failure","anomaly_score":0.88,"severity":"critical","is_anomaly":true}'
```

> "Here's a system failure - kernel panic. LogBERT detects this as Class 2."

**[Paste command 3 - Normal Log]**
```bash
curl -X POST http://localhost:8000/api/v1/logs/ \
  -H "X-API-Key: a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4" \
  -H "Content-Type: application/json" \
  -d '{"log_message":"GET /index.html HTTP/1.1 200 1234","timestamp":"2026-01-04 15:32:00","classification_class":0,"classification_name":"Normal","anomaly_score":0.05,"severity":"info","is_anomaly":false}'
```

> "And this normal HTTP request is correctly classified as benign with low anomaly score."

**[Refresh dashboard]**

> "Notice the anomaly count only increased for Security and System Failure - our intelligent filtering prevents alert fatigue."

---

### **[0:55 - 1:20] Real-Time Analytics (25 seconds)**

**[Navigate to Analytics page]**

> "The analytics dashboard provides real-time visualization of all log activity."

**[Point to Volume Chart]**
> "This chart shows log volume grouped by minute, with stacked bars representing all 7 LogBERT classifications: Normal, Security Anomaly, System Failure, Performance Issues, Network Anomalies, Configuration Issues, and Data Anomalies."

**[Point to Pie Chart]**
> "The classification distribution gives us an immediate overview of log types in the system."

**[Send multiple logs - have this ready in terminal]**
```bash
for i in {1..5}; do curl -s -X POST http://localhost:8000/api/v1/logs/ -H "X-API-Key: a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4" -H "Content-Type: application/json" -d "{\"log_message\":\"Sample log $i\",\"timestamp\":\"2026-01-04 15:35:0$i\",\"classification_class\":$((i % 7)),\"classification_name\":\"Class $((i % 7))\",\"anomaly_score\":0.5,\"severity\":\"info\",\"is_anomaly\":false}"; done
```

> "Let me send several more logs to demonstrate the real-time updates."

**[Click "Refresh Charts" button]**

> "The charts update instantly, showing the new log distribution."

---

### **[1:20 - 1:45] Key Features & Intelligence (25 seconds)**

**[Back to Dashboard - scroll through log table]**

> "Our key innovation is the intelligent anomaly detection logic. LogBERT classifies logs into 7 categories, but only Security Anomalies and System Failures trigger alerts. This is crucial for production environments - we track all log types for analysis, but only alert on critical issues.

> Each log entry shows the LogBERT classification, confidence score, severity level, and timestamp. The color-coded severity helps administrators quickly identify priority issues."

**[Point to Classification Stats on dashboard]**

> "The classification statistics provide a quick health check of the entire system."

---

### **[1:45 - 2:00] Conclusion (15 seconds)**

**[Show dashboard overview]**

> "As you can see, the system successfully classifies logs in real-time, intelligently filters critical anomalies, and provides actionable insights through our analytics dashboard. This completes our live demonstration. Thank you."

---

## 📋 Pre-Demo Checklist

### **Before Starting:**
- [ ] Clear database: `python3 manage.py shell` → `from dashboard.models import *; Anomaly.objects.all().delete(); LogEntry.objects.all().delete()`
- [ ] Start server: `python3 manage.py runserver`
- [ ] Set API key: `export LOGBERT_API_KEYS="a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4"`
- [ ] Login to dashboard: http://localhost:8000/dashboard/ (admin/admin123)
- [ ] Open analytics in new tab: http://localhost:8000/analytics/
- [ ] Prepare terminal with all curl commands ready
- [ ] Test one curl command to verify API key works

### **Terminal Setup:**
Open 2 terminals:
1. **Terminal 1:** Django server running
2. **Terminal 2:** Copy all curl commands ready to paste

### **Browser Setup:**
Open 2 tabs:
1. **Tab 1:** Dashboard (http://localhost:8000/dashboard/)
2. **Tab 2:** Analytics (http://localhost:8000/analytics/)

---

## 🎯 Key Points to Emphasize

1. **LogBERT Classification:** "Our fine-tuned BERT model classifies logs into 7 distinct categories"
2. **Intelligent Filtering:** "Only critical classes (Security & System Failure) create alerts"
3. **Real-Time Processing:** "Logs are classified and displayed in real-time"
4. **Scalability:** "Built on Kafka for handling high-volume log streams"
5. **Actionable Intelligence:** "Color-coded severity and confidence scores for quick decision-making"

---

## 💡 Talking Points (If Asked)

### **About LogBERT:**
- "LogBERT is a BERT model specifically fine-tuned on log data from multiple sources"
- "It achieves high accuracy in classifying log entries into 7 categories"
- "The model considers context and patterns that traditional regex-based parsers miss"

### **Why 7 Classifications:**
- "Based on industry-standard log categorization"
- "Covers: Normal operations, Security issues, System failures, Performance problems, Network anomalies, Configuration errors, and Data integrity issues"

### **Why Only 2 Create Alerts:**
- "To prevent alert fatigue - administrators need to focus on critical issues"
- "Performance and configuration issues are tracked for analysis but don't require immediate response"
- "Security and system failures need immediate attention"

### **Technical Stack:**
- "Kafka for distributed log collection"
- "LogBERT for AI-powered classification"
- "Django REST API for data ingestion"
- "Real-time analytics with Chart.js"
- "SQLite for development, easily scalable to PostgreSQL for production"

---

## 🎬 Quick Commands Reference

### Reset Database
```bash
python3 manage.py shell
```
```python
from dashboard.models import LogEntry, Anomaly
Anomaly.objects.all().delete()
LogEntry.objects.all().delete()
exit()
```

### All Demo Logs (Copy-Paste Block)
```bash
# Security Anomaly
curl -X POST http://localhost:8000/api/v1/logs/ -H "X-API-Key: a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4" -H "Content-Type: application/json" -d '{"log_message":"Failed password for admin from 192.168.1.100 port 22","timestamp":"2026-01-04 15:30:00","classification_class":1,"classification_name":"Security Anomaly","anomaly_score":0.92,"severity":"critical","is_anomaly":true}'

# System Failure
curl -X POST http://localhost:8000/api/v1/logs/ -H "X-API-Key: a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4" -H "Content-Type: application/json" -d '{"log_message":"Kernel panic - not syncing: Fatal exception","timestamp":"2026-01-04 15:31:00","classification_class":2,"classification_name":"System Failure","anomaly_score":0.88,"severity":"critical","is_anomaly":true}'

# Normal Log
curl -X POST http://localhost:8000/api/v1/logs/ -H "X-API-Key: a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4" -H "Content-Type: application/json" -d '{"log_message":"GET /index.html HTTP/1.1 200 1234","timestamp":"2026-01-04 15:32:00","classification_class":0,"classification_name":"Normal","anomaly_score":0.05,"severity":"info","is_anomaly":false}'

# Multiple logs
for i in {1..5}; do curl -s -X POST http://localhost:8000/api/v1/logs/ -H "X-API-Key: a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4" -H "Content-Type: application/json" -d "{\"log_message\":\"Sample log $i\",\"timestamp\":\"2026-01-04 15:35:0$i\",\"classification_class\":$((i % 7)),\"classification_name\":\"Class $((i % 7))\",\"anomaly_score\":0.5,\"severity\":\"info\",\"is_anomaly\":false}"; done
```

---

## ⏱️ Timing Breakdown

| Section | Time | Activity |
|---------|------|----------|
| Introduction | 0:00-0:15 | Brief intro, show empty dashboard |
| Security Log | 0:15-0:35 | Send & explain security anomaly |
| Multi-class | 0:35-0:55 | Send system failure & normal log |
| Analytics | 0:55-1:20 | Show charts, send bulk logs, refresh |
| Features | 1:20-1:45 | Explain intelligence, scroll logs |
| Conclusion | 1:45-2:00 | Summary & thank you |

---

## 🔥 Pro Tips

1. **Practice the curl commands** - know which one to paste when
2. **Use Cmd+Tab** (Mac) or Alt+Tab (Windows) to switch between terminal and browser smoothly
3. **Have dashboard refreshed** right before showing updates
4. **Point with cursor** when explaining charts - helps audience follow
5. **Speak clearly and steadily** - don't rush through technical terms
6. **Smile and make eye contact** - shows confidence
7. **Have backup plan** - if API fails, show the test results from run_local_tests.py

---

**You're Ready! 🚀 Good luck with your demo!**
