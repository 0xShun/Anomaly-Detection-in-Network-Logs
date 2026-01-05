# LogBERT Demo Quick Start Guide

## 🚀 Quick Demo Setup (3 Scripts)

### **Step 1: Start Kafka Services**
```bash
cd ~/develop/4\ mac/4\ mac/webplatform
./kafka_helper.sh start
./kafka_helper.sh create
```

### **Step 2: Start Consumer (with Model)**
```bash
# Terminal 2
cd ~/develop/4\ mac/4\ mac/webplatform
python3 kafka_consumer_api_sender.py --api-url https://logbert.pythonanywhere.com
```

### **Step 3: Send Demo Logs**
```bash
# Terminal 3 - Send to Kafka (goes through model)
cd ~/develop/4\ mac/4\ mac
python3 kafka_log_producer.py demo_logs/mixed_400.log 0.1

# OR - Send directly to PythonAnywhere (backup if model fails)
cd ~/develop/4\ mac/4\ mac/webplatform
python3 filebeat.py --remote
```

---

## 📊 Demo Flow

1. **Empty Dashboard** → Show clean state
2. **Run producer** → Logs flow: Kafka → Model → PythonAnywhere
3. **Watch real-time** → Anomalies populate in dashboard
4. **Threat Intelligence** → Click Security Anomaly IP → Lookup
5. **Threat Map** → Show global attack sources

---

## 🗺️ **NEW: Threat Intelligence Features**

### **A) Combined Threat Score (0-100)**
- **VirusTotal** (60 points) + **AbuseIPDB** (40 points)
- 🟢 **Safe** (0-30) | 🟡 **Suspicious** (31-70) | 🔴 **Malicious** (71-100)

### **C) GeoIP with Country Flags**
- Automatic flag emoji (🇺🇸 🇨🇳 🇷🇺)
- Country, city, ISP information
- AS Owner details

### **E) Global Threat Map**
- **Last 24 hours** security anomalies
- Color-coded markers by threat level
- Country summary statistics
- **Manual refresh** to update

---

## 🔑 API Keys (for PythonAnywhere WSGI)

```python
# Add to wsgi.py on PythonAnywhere:
os.environ['VIRUSTOTAL_API_KEY'] = '1fe87da3caa60ed71dceed86dd29985f850917ad0176605c346e8fdb5a7a530a'
os.environ['ABUSEIPDB_API_KEY'] = 'bb6962832801414a2aa14136f0e34505dd332eabf78d1c00488d352c7b9aeff97253578a2f1ca84b'
os.environ['SHODAN_API_KEY'] = 'HJSUhWecNSTmamIXIqyMDeo9VOZ50EMY'
```

---

## 📝 Demo Log File Details

**Location:** `~/develop/4 mac/4 mac/demo_logs/mixed_400.log`

**Content:**
- **400 total logs**
- **Mixed sources:** Apache access logs + Linux syslog + Firewall logs
- **24 malicious IPs** for threat intelligence demo
- **10 firewall anomaly logs** (DENY rules, brute force, DDoS, exploits)

**Malicious IPs included:**
```
222.189.195.176, 42.0.135.109, 23.95.35.112, 185.220.101.34,
103.253.145.22, 91.134.127.228, 194.169.175.49, 178.128.227.185,
198.98.57.207, 61.177.172.84, 159.203.104.142, 89.248.172.16,
141.98.10.60, 95.214.26.70, 212.70.149.76, 185.234.218.25,
43.240.221.119, 185.220.102.8, 80.94.95.162, 123.126.113.94,
106.75.190.11, 46.161.40.37, 117.26.242.10, 62.102.148.68,
101.200.81.187, 139.59.253.62, 198.143.32.65, 64.227.14.149,
71.6.165.200, 47.254.173.65, 104.168.155.129, 167.248.133.40,
80.82.77.139, 110.34.32.92, 51.79.82.21, 195.211.160.53
```

---

## 🎥 Recording Tips

1. **Prepare:** Clear dashboard, start all services
2. **Narrate:** Follow `DEMO_SCRIPT.md` timing (2 minutes)
3. **Highlight:**
   - Real-time log classification
   - Color-coded severity badges
   - Combined threat scoring
   - Geographic threat visualization
4. **Impress:** Show 100/100 threat score on malicious IP

---

## 🛑 Stop Services

```bash
# Kafka (press Ctrl+C in terminals)
# Or use:
pkill -f kafka
pkill -f zookeeper
```

---

## ✅ Checklist Before Recording

- [ ] Kafka started and topic created
- [ ] Consumer running with model loaded
- [ ] Django server on localhost:8080 OR PythonAnywhere
- [ ] Dashboard empty and ready
- [ ] Browser at http://localhost:8080/dashboard/ (or logbert.pythonanywhere.com)
- [ ] Demo script open (DEMO_SCRIPT.md)
- [ ] Screen recorder ready

**Good luck with your demo! 🎬**
