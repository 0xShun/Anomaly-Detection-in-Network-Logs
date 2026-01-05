#!/usr/bin/env python3
"""
Demo Log Generator - Sends 400 realistic classified logs to API
Simulates logs that have been classified by LogBERT model

Usage:
    python3 filebeat.py              # Send to local server (localhost:8080)
    python3 filebeat.py --remote     # Send to PythonAnywhere (logbert.pythonanywhere.com)
"""

import requests
import time
from datetime import datetime, timedelta
import random
import sys
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Send demo logs to API')
parser.add_argument('--remote', action='store_true', 
                    help='Send to PythonAnywhere instead of localhost')
args = parser.parse_args()

# API Configuration
if args.remote:
    API_URL = "https://logbert.pythonanywhere.com/api/v1/logs/"
    API_KEY = "a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4"
    print("🌐 Remote mode: Sending to PythonAnywhere")
else:
    API_URL = "http://localhost:8080/api/v1/logs/"
    API_KEY = "C6lMbC13jaElZ_tFjuTHfg_ywDzyAvJHl7W2efpNqCA"
    print("💻 Local mode: Sending to localhost:8080")

# Log templates for each classification
LOG_TEMPLATES = {
    0: [  # Normal - 60% of logs
        "GET /index.html HTTP/1.1 200 {size}",
        "POST /api/login HTTP/1.1 200 OK",
        "User {user} logged in successfully",
        "Database query completed in {time}ms",
        "File {file} uploaded successfully",
        "Service started on port {port}",
        "Backup completed successfully",
        "Cache cleared for user {user}",
        "Email sent to {email}",
        "Configuration reloaded",
    ],
    1: [  # Security Anomaly - 15% of logs
        "Failed password for admin from {ip} port 22 ssh2",
        "Invalid user admin from {ip}",
        "Rejected connection from {ip}",
        "Multiple failed login attempts from {ip}",
        "Unauthorized access attempt to {path}",
        "Brute force attack detected from {ip}",
        "SQL injection attempt blocked",
        "Suspicious file upload from {ip}",
        "Port scanning detected from {ip}",
        "XSS attack prevented on {path}",
    ],
    2: [  # System Failure - 5% of logs
        "Kernel panic - not syncing: Fatal exception",
        "Out of memory: Kill process {pid}",
        "Segmentation fault at address {addr}",
        "Critical: Disk {disk} failure detected",
        "Database connection lost",
        "Service {service} crashed with signal 11",
        "RAID array degraded on {device}",
        "System reboot required - critical update",
        "File system corruption detected on {device}",
        "Hardware error: CPU {cpu} throttling",
    ],
    3: [  # Performance Issue - 10% of logs
        "High CPU usage detected: {percent}%",
        "Memory usage critical: {percent}%",
        "Slow database query: {time}ms",
        "Request timeout after {seconds}s",
        "Disk I/O wait time high: {percent}%",
        "Network latency increased to {ms}ms",
        "Thread pool exhausted: {count} threads",
        "Connection pool at capacity",
        "Swap usage at {percent}%",
        "Response time exceeded threshold: {time}ms",
    ],
    4: [  # Network Anomaly - 5% of logs
        "Network timeout on interface {interface}",
        "High packet loss detected: {percent}%",
        "DNS resolution failed for {domain}",
        "Connection refused on port {port}",
        "Unusual traffic pattern from {ip}",
        "DDoS attack suspected from {ip}",
        "Network interface {interface} down",
        "Bandwidth limit exceeded",
        "TCP retransmission rate high",
        "ARP spoofing detected from {ip}",
    ],
    5: [  # Configuration Issue - 3% of logs
        "Configuration file {file} syntax error",
        "Missing required parameter: {param}",
        "Invalid configuration value for {key}",
        "Configuration conflict detected",
        "Deprecated setting used: {setting}",
        "Configuration backup failed",
        "Environment variable {var} not set",
        "SSL certificate expired",
        "Invalid database connection string",
        "Port {port} already in use",
    ],
    6: [  # Data Anomaly - 2% of logs
        "Data validation failed for field {field}",
        "Duplicate entry detected in {table}",
        "Data integrity check failed",
        "Unexpected NULL value in {column}",
        "Foreign key constraint violation",
        "Data type mismatch in {field}",
        "Checksum verification failed",
        "Orphaned records found in {table}",
        "Data synchronization error",
        "Invalid JSON format in request",
    ]
}

# Severity mapping for each class
SEVERITY_MAP = {
    0: ["info", "low"],
    1: ["critical", "high"],
    2: ["critical"],
    3: ["medium", "high"],
    4: ["medium", "high"],
    5: ["low", "medium"],
    6: ["medium", "low"]
}

# Anomaly score ranges
ANOMALY_SCORE_RANGES = {
    0: (0.01, 0.15),   # Normal - low scores
    1: (0.85, 0.99),   # Security - high scores
    2: (0.80, 0.95),   # System Failure - high scores
    3: (0.55, 0.75),   # Performance - medium scores
    4: (0.60, 0.80),   # Network - medium-high scores
    5: (0.45, 0.65),   # Configuration - medium scores
    6: (0.50, 0.70)    # Data - medium scores
}

# IP pools
NORMAL_IPS = [f"192.168.1.{i}" for i in range(10, 100)]
MALICIOUS_IPS = [
    # China
    "222.189.195.176",  # CN - Known malicious
    "42.0.135.109",     # CN - Scanning/attacks
    "42.0.136.11",      # CN - Brute force
    "223.167.143.37",   # CN - DDoS
    "116.208.206.150",  # CN - Exploitation
    "117.60.41.169",    # CN - Malicious activity
    "106.111.126.156",  # CN - Port scanning
    "120.39.55.74",     # CN - Attack source
    "113.231.14.218",   # CN - Malicious
    
    # United States
    "23.95.35.112",     # US - Malicious activity
    "162.19.231.60",    # US - Known bad actor
    "63.223.81.61",     # US - Attack source
    "23.222.22.159",    # US - Scanning
    
    # Russia
    "185.220.101.34",   # RU - Tor exit node
    "91.219.237.244",   # RU - DDoS attacks
    "89.248.165.188",   # RU - Malicious host
    "45.155.205.233",   # RU - Brute force
    "185.156.73.54",    # RU - Attack source
    
    # Germany
    "195.201.151.226",  # DE - Scanning/attacks
    "178.254.13.177",   # DE - Malicious activity
    "88.198.48.20",     # DE - Known bad IP
    
    # India
    "103.253.145.22",   # IN - Brute force
    "103.105.50.50",    # IN - Malicious
    "152.58.182.221",   # IN - Attack source
    
    # Brazil
    "177.11.51.73",     # BR - Malicious activity
    "189.6.6.197",      # BR - DDoS source
    
    # France
    "51.255.172.55",    # FR - Attack source
    "178.33.111.174",   # FR - Malicious
    
    # Netherlands
    "198.50.191.95",    # NL - Malicious host
    "185.220.101.42",   # NL - Tor exit/attacks
    
    # Vietnam
    "113.161.88.153",   # VN - Attack source
    
    # Singapore
    "188.166.234.197",  # SG - Malicious activity
    
    # Turkey
    "185.129.61.46",    # TR - Attack source
    
    # Poland
    "91.134.232.137",   # PL - Malicious
    
    # Ukraine
    "176.103.48.107",   # UA - DDoS/attacks
    
    # South Korea
    "211.253.10.86",    # KR - Scanning
    
    # Thailand
    "171.6.120.45",     # TH - Malicious activity
    
    # Bangladesh
    "103.106.239.71",   # BD - Attack source
]

def generate_log_message(classification_class):
    """Generate realistic log message based on classification"""
    template = random.choice(LOG_TEMPLATES[classification_class])
    
    # Fill in template variables
    replacements = {
        'size': random.randint(1000, 50000),
        'user': random.choice(['admin', 'user1', 'john', 'sarah', 'system']),
        'time': random.randint(10, 5000),
        'file': random.choice(['report.pdf', 'image.jpg', 'data.csv', 'config.xml']),
        'port': random.choice([22, 80, 443, 3306, 5432, 8080]),
        'email': f"user{random.randint(1,100)}@example.com",
        'ip': random.choice(MALICIOUS_IPS if classification_class in [1, 4] else NORMAL_IPS),
        'path': random.choice(['/admin', '/api/users', '/config', '/data']),
        'pid': random.randint(1000, 9999),
        'addr': hex(random.randint(0x1000, 0xFFFF)),
        'disk': random.choice(['sda', 'sdb', 'nvme0n1']),
        'device': random.choice(['/dev/sda1', '/dev/sdb2', '/dev/md0']),
        'service': random.choice(['nginx', 'mysql', 'postgresql', 'redis']),
        'cpu': random.randint(0, 7),
        'percent': random.randint(85, 99),
        'seconds': random.randint(30, 120),
        'ms': random.randint(200, 2000),
        'count': random.randint(100, 500),
        'interface': random.choice(['eth0', 'eth1', 'wlan0']),
        'domain': random.choice(['api.example.com', 'db.internal', 'cache.local']),
        'param': random.choice(['database_url', 'api_key', 'secret_token']),
        'key': random.choice(['max_connections', 'timeout', 'buffer_size']),
        'setting': random.choice(['ssl_v2', 'tls_1.0', 'md5_hash']),
        'var': random.choice(['DATABASE_URL', 'SECRET_KEY', 'API_TOKEN']),
        'field': random.choice(['email', 'username', 'amount', 'date']),
        'table': random.choice(['users', 'orders', 'products', 'logs']),
        'column': random.choice(['user_id', 'created_at', 'status'])
    }
    
    message = template
    for key, value in replacements.items():
        message = message.replace(f'{{{key}}}', str(value))
    
    return message

def generate_log(classification_class, timestamp):
    """Generate a complete log entry"""
    message = generate_log_message(classification_class)
    severity = random.choice(SEVERITY_MAP[classification_class])
    min_score, max_score = ANOMALY_SCORE_RANGES[classification_class]
    anomaly_score = round(random.uniform(min_score, max_score), 4)
    
    # Only classes 1 and 2 are marked as anomalies
    is_anomaly = classification_class in [1, 2]
    
    # Select IP based on classification
    if classification_class == 1:  # Security Anomaly - use malicious IPs
        host_ip = random.choice(MALICIOUS_IPS)
    elif classification_class == 4:  # Network Anomaly - mix of malicious and normal
        host_ip = random.choice(MALICIOUS_IPS + NORMAL_IPS)
    else:
        host_ip = random.choice(NORMAL_IPS)
    
    # Classification names
    class_names = {
        0: "Normal",
        1: "Security Anomaly",
        2: "System Failure",
        3: "Performance Issue",
        4: "Network Anomaly",
        5: "Configuration Issue",
        6: "Data Anomaly"
    }
    
    return {
        "log_message": message,
        "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        "host_ip": host_ip,
        "source": random.choice(['linux', 'apache', 'nginx', 'mysql', 'system']),
        "log_type": "ERROR" if classification_class in [1, 2] else ("WARNING" if classification_class in [3, 4] else "INFO"),
        "classification_class": classification_class,
        "classification_name": class_names[classification_class],
        "anomaly_score": anomaly_score,
        "severity": severity,
        "is_anomaly": is_anomaly
    }

def send_log(log_data, log_number, total_logs):
    """Send a single log to the API"""
    try:
        headers = {
            'X-API-Key': API_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(API_URL, json=log_data, headers=headers, timeout=5)
        
        if response.status_code == 201:
            # Print the actual log message being sent (simulate VM output)
            log_msg = log_data['log_message']
            timestamp = log_data['timestamp'].split('T')[1].split('.')[0]  # Extract time only
            print(f"[  {timestamp}  ] {log_msg}")
            return True
        else:
            print(f"[  ERROR  ] Failed to send log: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[  ERROR  ] {e}")
        return False

def main():
    """Main function to generate and send 400 logs"""
    
    # QEMU/Linux boot header
    print("\n" + "=" * 80)
    print("QEMU Virtual Machine Monitor")
    print("=" * 80)
    print(f"Starting QEMU system x86_64 v7.2.0")
    print(f"Network backend: user mode")
    print(f"Log forwarding: {API_URL}")
    print("=" * 80)
    print()
    
    # Linux boot messages
    print("[    0.000000] Linux version 6.1.0-logbert (root@logbert-vm)")
    print("[    0.000000] Command line: BOOT_IMAGE=/boot/vmlinuz root=/dev/sda1")
    print("[    0.000000] x86/fpu: Supporting XSAVE feature 0x001: 'x87 floating point'")
    print("[    0.001234] Memory: 4096MB available")
    print("[    0.002456] CPU: Intel(64) Family 6 Model 142 Stepping 12")
    print("[    0.005678] smpboot: Allowing 4 CPUs, 0 hotplug CPUs")
    print("[    0.012345] Setting up swiotlb for DMA bounce buffers")
    print("[    0.023456] PCI: Using configuration type 1 for base access")
    print("[    0.034567] workingset: timestamp_bits=14 max_order=18")
    print("[    0.045678] Block layer SCSI generic (bsg) driver version 0.4")
    print("[    0.056789] Serial: 8250/16550 driver, 4 ports, IRQ sharing enabled")
    print("[    0.067890] Non-volatile memory driver v1.3")
    print("[    0.078901] Linux agpgart interface v0.103")
    print("[    0.089012] ACPI: bus type USB registered")
    print("[    0.100123] usbcore: registered new interface driver usbfs")
    print("[    0.111234] SCSI subsystem initialized")
    print("[    0.122345] Initializing random number generator")
    print("[    0.133456] alg: No test for lzo-rle (lzo-rle-generic)")
    print("[    0.144567] NET: Registered PF_INET protocol family")
    print("[    0.155678] TCP established hash table entries: 32768")
    print("[    0.166789] TCP bind hash table entries: 32768")
    print("[    0.177890] Initializing cgroup subsys cpuset")
    print("[    0.188901] Initializing cgroup subsys cpu")
    print("[    0.199012] Initializing cgroup subsys cpuacct")
    print("[    0.210123] EXT4-fs (sda1): mounted filesystem with ordered data mode")
    print("[    0.221234] VFS: Mounted root (ext4 filesystem) readonly")
    print("[    0.232345] devtmpfs: mounted")
    print("[    0.243456] Freeing unused kernel memory: 1024K")
    print("[    0.254567] systemd[1]: systemd 252 running in system mode")
    print("[    0.265678] systemd[1]: Detected virtualization qemu")
    print("[    0.276789] systemd[1]: Detected architecture x86-64")
    print("[    0.287890] systemd[1]: Set hostname to <logbert-vm>")
    print("[    0.298901] systemd[1]: Reached target Basic System")
    print("[    0.309012] systemd[1]: Starting Network Service...")
    print("[    0.320123] systemd[1]: Starting OpenSSH server daemon...")
    print("[    0.331234] systemd[1]: Starting System Logging Service...")
    print("[    0.342345] systemd[1]: Started rsyslog.service")
    print("[    0.353456] rsyslogd: [origin software=\"rsyslogd\" version=\"8.2302.0\"]")
    print()
    print("[    0.365000] LogBERT Monitoring Agent v2.1.0 initialized")
    print("[    0.365500] Connecting to central log collection endpoint...")
    print("[    0.366000] Connection established. Beginning log stream...")
    print()
    
    # Distribution of log types (totals to 400)
    distribution = {
        0: 240,  # 60% Normal
        1: 60,   # 15% Security Anomaly
        2: 20,   # 5% System Failure
        3: 40,   # 10% Performance Issue
        4: 20,   # 5% Network Anomaly
        5: 12,   # 3% Configuration Issue
        6: 8     # 2% Data Anomaly
    }
    
    # Generate all logs first
    all_logs = []
    start_time = datetime.now() - timedelta(hours=2)  # Start from 2 hours ago
    
    for class_id, count in distribution.items():
        for i in range(count):
            # Spread logs over 2 hours with some randomness
            time_offset = timedelta(
                seconds=random.randint(0, 7200)  # Random time within 2 hours
            )
            timestamp = start_time + time_offset
            log = generate_log(class_id, timestamp)
            all_logs.append(log)
    
    # Shuffle to mix different types
    random.shuffle(all_logs)
    
    # Sort by timestamp for realistic chronological order
    all_logs.sort(key=lambda x: x['timestamp'])
    
    success_count = 0
    start = time.time()
    
    for i, log in enumerate(all_logs, 1):
        if send_log(log, i, len(all_logs)):
            success_count += 1
        
        # Small delay to simulate real-time log generation
        time.sleep(0.05)  # 50ms delay between requests
    
    elapsed = time.time() - start
    
    print()
    print("[    {:.6f}] Log stream completed".format(elapsed + 0.366))
    print("[    {:.6f}] Connection closed gracefully".format(elapsed + 0.367))
    print()
    print("=" * 80)
    print("SYSTEM STATUS")
    print("=" * 80)
    print(f"Total logs transmitted: {len(all_logs)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(all_logs) - success_count}")
    print(f"Runtime: {elapsed:.2f} seconds")
    print(f"Transmission rate: {len(all_logs)/elapsed:.2f} logs/second")
    print()
    print("✓ System monitoring active. Dashboard: https://logbert.pythonanywhere.com/dashboard/")
    print("=" * 80)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[  SIGINT  ] Interrupt signal received")
        print("[  SHUTDOWN  ] Stopping log transmission...")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[  CRITICAL  ] System error: {e}")
        sys.exit(1)
