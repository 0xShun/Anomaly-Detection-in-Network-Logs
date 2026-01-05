# Threat Intelligence Cache Population Guide

## Overview
The `populate_threat_cache.py` script automatically looks up all unique IPs from Security Anomaly logs and caches their threat intelligence data. This populates the Global Threat Map with markers.

## Running on PythonAnywhere

### Step 1: Pull Latest Code
```bash
cd ~/Anomaly-Detection-in-Network-Logs/webplatform
git pull origin main
```

### Step 2: Run the Script
```bash
python3 populate_threat_cache.py
```

### What It Does
1. Finds all unique IPs from Security Anomaly logs (last 24 hours)
2. Checks which ones are already cached
3. Looks up uncached IPs via VirusTotal, AbuseIPDB, and Shodan
4. Saves results to `ThreatIntelligenceCache` table
5. Displays progress and summary

### Example Output
```
================================================================================
THREAT INTELLIGENCE CACHE POPULATOR
================================================================================

📊 Found 15 unique IPs in Security Anomaly logs
✅ Already cached: 3
🔍 Need to lookup: 12

🚀 Looking up 12 IPs...
⚠️  Note: API rate limits apply. This may take a few minutes.

[1/12] Looking up 222.189.195.176... ✅ Cached
[2/12] Looking up 185.220.101.34... ✅ Cached
[3/12] Looking up 23.95.35.112... ✅ Cached
...

================================================================================
SUMMARY
================================================================================
✅ Successfully cached: 12
❌ Errors/Skipped: 0
📊 Total in cache: 15

🎉 Done! Refresh the Threat Map to see markers.
================================================================================
```

### Step 3: View Results
1. Go to https://logbert.pythonanywhere.com/dashboard/threat-intelligence/
2. Scroll to "Global Threat Map" section
3. Click "Refresh" button
4. See markers appear on the world map! 🗺️

## Rate Limits
- **VirusTotal**: 4 requests/minute (free tier)
- **AbuseIPDB**: 1000 requests/day
- **Shodan**: 100 requests/month (free tier)

The script handles rate limits automatically and will skip/retry as needed.

## Cache Duration
- Cached data expires after **7 days**
- Running the script again will only look up expired entries
- Saves API quota by reusing cached data

## Manual Lookup (Alternative)
If you prefer to populate manually through the web UI:

**Top Malicious IPs to Look Up:**
```
222.189.195.176  (China - Known malicious)
185.220.101.34   (Tor exit node)
23.95.35.112     (US - Malicious activity)
42.0.135.109     (China - Scanning/attacks)
103.253.145.22   (Bangladesh - Brute force)
198.50.191.95    (Canada - Malicious host)
91.219.237.244   (Netherlands - Scanning)
45.155.205.233   (Russia - DDoS/attacks)
162.142.125.221  (US - Exploited host)
89.248.165.188   (Russia - Malicious)
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'django'"
Make sure you're running on PythonAnywhere where Django is installed, not locally.

### "No Security Anomaly IPs found"
Run `filebeat.py --remote` first to send logs to PythonAnywhere.

### API Key Errors
Verify API keys are set in PythonAnywhere WSGI configuration:
- `VIRUSTOTAL_API_KEY`
- `ABUSEIPDB_API_KEY`
- `SHODAN_API_KEY`

### Rate Limit Errors
Wait a few minutes and run the script again. Already-cached IPs will be skipped.

## Demo Recording Tips
1. Clear old cache: Delete `ThreatIntelligenceCache` entries via Django admin
2. Send demo logs: `python3 filebeat.py --remote`
3. Populate cache: `python3 populate_threat_cache.py`
4. Show threat map with markers during recording
5. Click markers to show IP details in popups
