# Unified Threat Intelligence Setup Guide

## Overview
The platform now integrates three threat intelligence services for comprehensive IP address analysis:
- **VirusTotal** - Malware detection and IP reputation
- **AbuseIPDB** - IP abuse reports and confidence scoring
- **Shodan** - Internet-connected device intelligence and vulnerability scanning

## Features Implemented

### 1. **Unified Lookup Interface**
   - Single search bar that queries all 3 services simultaneously
   - Results displayed in organized service-specific cards
   - Displays: threat levels, vulnerability counts, abuse reports, open ports, CVEs, etc.

### 2. **Smart Caching System**
   - Automatically caches results for 7 days
   - Prevents redundant API calls
   - Reduces risk of hitting rate limits
   - Shows cache age in results

### 3. **Rate Limiting**
   - **VirusTotal**: 4 requests/minute, 500/day
   - **AbuseIPDB**: 1,000 requests/day
   - **Shodan**: 1 request/second, 100/month
   - Automatic tracking and enforcement
   - User-friendly error messages when limits reached

### 4. **Database Storage**
   - New `ThreatIntelligenceCache` model stores all data
   - Indexed for fast lookups
   - Admin interface for cache management

## Setup Instructions

### Step 1: Get API Keys

#### VirusTotal (Free Tier)
1. Go to: https://www.virustotal.com/gui/join-us
2. Create a free account
3. Navigate to your profile → API Key
4. Copy your API key
5. Limits: 4 requests/minute, 500/day

#### AbuseIPDB (Free Tier)
1. Go to: https://www.abuseipdb.com/register
2. Create a free account
3. Navigate to Account → API
4. Generate an API key
5. Copy your API key
6. Limits: 1,000 requests/day

#### Shodan (Free Tier)
1. Go to: https://account.shodan.io/register
2. Create a free account
3. Navigate to Account → API Key
4. Copy your API key
5. Limits: 1 request/second, 100/month
6. Note: Paid plans offer more features

### Step 2: Configure Environment Variables

Edit your `.env` file in `/home/shun/Desktop/logbert/webplatform/.env`:

```bash
# Threat Intelligence API Keys
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here
ABUSEIPDB_API_KEY=your_abuseipdb_api_key_here
SHODAN_API_KEY=your_shodan_api_key_here
```

**Important**: 
- Replace the placeholder values with your actual API keys
- Keep your `.env` file secure and never commit it to version control
- The `.env.template` file has been updated with these fields

### Step 3: Restart Django Server

After adding API keys:
```bash
cd /home/shun/Desktop/logbert/webplatform
source venv/bin/activate
python manage.py runserver
```

## Usage

### Access the Threat Intelligence Page
1. Log in to the dashboard
2. Navigate to: **Threat Intelligence** in the navigation menu
3. Or go directly to: `http://localhost:8000/dashboard/threat-intelligence/`

### Lookup an IP Address
1. Enter an IPv4 address in the search box
2. Click "Check All Services"
3. Wait a few seconds while all 3 services are queried
4. View comprehensive results from all services

### Quick Lookup from Anomalies
- Recent anomaly IPs appear as clickable badges below the search
- Click any IP to instantly look it up

### Understanding Results

#### VirusTotal Section
- **Malicious/Suspicious Counts**: Number of security vendors flagging the IP
- **Reputation Score**: Community-based reputation (-100 to +100)
- **Country/ASN**: Geographic and network information
- **Detection Engines**: List of vendors that flagged it

#### AbuseIPDB Section
- **Confidence Score**: 0-100% likelihood of being malicious
  - 0% = Clean
  - 1-50% = Suspicious
  - 51-100% = High Risk
- **Total Reports**: Number of abuse reports
- **Categories**: Types of abuse (DDoS, SSH attack, spam, etc.)
- **Whitelist Status**: If IP is known-good

#### Shodan Section
- **Open Ports**: Publicly accessible network ports
- **Vulnerabilities**: Known CVEs affecting the host
- **Services**: Software/services running on the IP
- **Organization**: Company/ISP owning the IP
- **Hostnames**: Domain names associated with the IP

### Cached Results
- If data is cached, you'll see a "Cached data (X days old)" badge
- Cache expires after 7 days
- Fresh queries are made automatically when cache expires
- This helps conserve API quota

## Rate Limit Management

The system automatically tracks and enforces rate limits:

### When Rate Limit is Reached:
- You'll see an error message indicating which service hit the limit
- The message shows how long to wait
- Other services (not rate-limited) will still show results

### Best Practices:
1. **Avoid spamming lookups** - use the cached results when available
2. **Prioritize important IPs** - check high-severity anomalies first
3. **Shodan is most limited** (100/month) - use sparingly
4. **Check cache in admin panel** to see what's already looked up

## Admin Interface

### View Cached Threat Intelligence
1. Go to Django admin: `http://localhost:8000/admin/`
2. Navigate to: **Dashboard → Threat Intelligence Cache**
3. Search by IP address
4. Filter by query date
5. View all stored data for each IP

### Clear Cache (if needed)
- Select cached entries in admin
- Use "Delete selected" action
- This will force fresh lookups on next search

## Troubleshooting

### "API key not configured" Error
- **Solution**: Make sure you've added all three API keys to your `.env` file
- Restart the Django server after adding keys

### "Rate limit exceeded" Error
- **Solution**: Wait the specified time before trying again
- Use cached results when available
- Consider upgrading API plan if you need more quota

### No Shodan Data
- Many IPs won't have Shodan data (normal behavior)
- Shodan only indexes publicly accessible hosts
- You'll see "No Shodan data available" message

### Missing Service Results
- If one service fails, others will still show results
- Check the error message for the specific service
- Common causes: API key invalid, network issues, rate limits

## Database Migrations

Already applied! But if you need to reapply:
```bash
cd /home/shun/Desktop/logbert/webplatform
source venv/bin/activate
python manage.py makemigrations dashboard
python manage.py migrate dashboard
```

## File Changes Summary

### New Files:
- `dashboard/threat_intel_utils.py` - Core threat intelligence logic
- `dashboard/migrations/0004_threatintelligencecache.py` - Database migration

### Modified Files:
- `dashboard/models.py` - Added `ThreatIntelligenceCache` model
- `dashboard/views.py` - Updated `virustotal_lookup()` to unified lookup
- `dashboard/admin.py` - Registered new model
- `templates/dashboard/threat_intelligence.html` - Complete UI rewrite
- `.env.template` - Added new API key fields

## API Key Security

### Important Security Notes:
1. **Never commit `.env` file** to version control
2. **Use strong, unique API keys** for each service
3. **Rotate keys periodically** (every 6-12 months)
4. **Monitor usage** through each service's dashboard
5. **Restrict API key permissions** if available

### For Production Deployment:
- Set `DEBUG=False` in settings
- Use environment variables on PythonAnywhere
- Enable HTTPS for all traffic
- Implement user authentication requirements
- Consider adding IP whitelisting for API endpoints

## Next Steps

1. **Get your API keys** from all three services
2. **Add them to `.env` file**
3. **Restart Django server**
4. **Test with a known malicious IP** (e.g., from recent anomalies)
5. **Review cached results** in admin panel

## Support

If you encounter issues:
1. Check Django logs: `webplatform/django.log`
2. Verify API keys are correct
3. Test each API individually (check their documentation)
4. Ensure virtual environment is activated
5. Check that migrations were applied successfully

## API Rate Limit Summary

| Service | Free Tier Limits | Upgrade Options |
|---------|-----------------|-----------------|
| VirusTotal | 4/min, 500/day | Premium: $99/mo+ |
| AbuseIPDB | 1,000/day | Premium: $20/mo+ |
| Shodan | 1/sec, 100/mo | Membership: $59/mo |

For production use with high volume, consider upgrading at least one service.
