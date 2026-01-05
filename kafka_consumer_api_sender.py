#!/usr/bin/env python3
"""
Kafka Consumer that sends log classifications to PythonAnywhere API

This script:
1. Consumes logs from Kafka topic
2. Classifies them using Hybrid-BERT model
3. Sends classification results to PythonAnywhere API endpoint
4. Works on both macOS and Linux

Usage:
    python3 kafka_consumer_api_sender.py --api-url https://yoursite.pythonanywhere.com
    
Environment Variables:
    KAFKA_BOOTSTRAP_SERVERS (optional): Kafka servers, default: localhost:9092
    KAFKA_TOPIC (optional): Kafka topic name, default: log_topic
    API_URL (optional): PythonAnywhere API URL
"""

import os
import sys
import json
import time
import logging
import argparse
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
import re

# Check required dependencies
def check_dependencies():
    """Check if required packages are installed"""
    required_packages = {
        'kafka': 'kafka-python',
        'requests': 'requests',
        'dateutil': 'python-dateutil'
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print(f"Install with: pip3 install {' '.join(missing)}")
        sys.exit(1)

check_dependencies()

# Now import after check
from kafka import KafkaConsumer
import requests
from dateutil import parser as date_parser

# Import model manager
from dashboard.ml_utils import HybridBERTModelManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class KafkaToAPIConsumer:
    """Consumes logs from Kafka and sends to API"""
    
    def __init__(self, api_url: str, kafka_servers: str = 'localhost:9092', 
                 topic: str = 'log_topic', api_key: str = None):
        self.api_url = api_url.rstrip('/') + '/api/logs/'
        self.kafka_servers = kafka_servers
        self.topic = topic
        self.api_key = api_key or 'a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4'
        self.model_manager = None
        self.hostname_to_ip = {}
        
        logger.info(f"Initializing Kafka consumer...")
        logger.info(f"Kafka servers: {self.kafka_servers}")
        logger.info(f"Topic: {self.topic}")
        logger.info(f"API endpoint: {self.api_url}")
        logger.info(f"API key: {self.api_key[:20]}...")
        
        
    def load_model(self):
        """Load Hybrid-BERT model"""
        logger.info("Loading Hybrid-BERT model (this may take 30-60 seconds)...")
        try:
            self.model_manager = HybridBERTModelManager()
            logger.info("✅ Model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    def _generate_ip_from_hostname(self, hostname: str) -> str:
        """Generate consistent IP address from hostname using MD5 hash"""
        if hostname in self.hostname_to_ip:
            return self.hostname_to_ip[hostname]
        
        # Generate IP from hostname hash
        hash_obj = hashlib.md5(hostname.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Use first 8 hex chars to create IP
        ip = f"192.168.{int(hash_hex[0:2], 16) % 256}.{int(hash_hex[2:4], 16) % 256}"
        self.hostname_to_ip[hostname] = ip
        return ip
    
    def _extract_ip(self, log_text: str) -> str:
        """Extract IP address from log message"""
        # IPv4 pattern
        ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ipv4_matches = re.findall(ipv4_pattern, log_text)
        if ipv4_matches:
            return ipv4_matches[0]
        
        # Try to extract hostname for Linux logs
        hostname_patterns = [
            r'^(\S+)\s+',  # First word (hostname)
            r'from\s+(\S+)',  # "from hostname"
        ]
        
        for pattern in hostname_patterns:
            match = re.search(pattern, log_text)
            if match:
                hostname = match.group(1)
                # Skip common non-hostname words
                if hostname.lower() not in ['info', 'error', 'warning', 'debug']:
                    return self._generate_ip_from_hostname(hostname)
        
        return "unknown"
    
    def _parse_apache_log(self, log_text: str) -> Dict[str, Any]:
        """Parse Apache access log"""
        # Apache combined log format
        pattern = r'^(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d{3}) (\d+|-) "([^"]*)" "([^"]*)"'
        match = re.match(pattern, log_text)
        
        if match:
            ip = match.group(1)
            timestamp_str = match.group(2)
            
            # Parse timestamp
            try:
                timestamp = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
            except:
                timestamp = datetime.now()
            
            return {
                'host_ip': ip,
                'timestamp': timestamp,
                'log_type': 'apache',
                'source': 'apache'
            }
        
        # Fallback
        return {
            'host_ip': self._extract_ip(log_text),
            'timestamp': datetime.now(),
            'log_type': 'apache',
            'source': 'apache'
        }
    
    def _parse_linux_log(self, log_text: str) -> Dict[str, Any]:
        """Parse Linux syslog format"""
        # Try common syslog formats
        patterns = [
            r'^(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)',  # Month Day HH:MM:SS hostname
            r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',  # ISO format
        ]
        
        timestamp = datetime.now()
        hostname = None
        
        for pattern in patterns:
            match = re.match(pattern, log_text)
            if match:
                try:
                    timestamp = date_parser.parse(match.group(1))
                    if len(match.groups()) > 1:
                        hostname = match.group(2)
                    break
                except:
                    pass
        
        ip = self._extract_ip(log_text)
        
        return {
            'host_ip': ip,
            'timestamp': timestamp,
            'log_type': 'syslog',
            'source': 'linux'
        }
    
    def _parse_log_entry(self, log_text: str) -> Dict[str, Any]:
        """Parse log entry and extract metadata"""
        # Detect log type
        if re.match(r'^\S+\s+\S+\s+\S+\s+\[', log_text):  # Apache format
            return self._parse_apache_log(log_text)
        else:  # Assume Linux syslog
            return self._parse_linux_log(log_text)
    
    def send_to_api(self, log_data: Dict[str, Any], max_retries: int = 4, 
                    retry_delay: int = 2) -> bool:
        """
        Send log data to API with retry logic (fire-and-forget)
        
        Args:
            log_data: Dictionary with log and classification data
            max_retries: Maximum number of retry attempts (default: 4)
            retry_delay: Delay between retries in seconds (default: 2)
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Convert datetime to string
        if isinstance(log_data.get('timestamp'), datetime):
            log_data['timestamp'] = log_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Prepare headers with API key authentication
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    self.api_url,
                    json=log_data,
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 201:
                    return True
                else:
                    logger.warning(f"API returned status {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"❌ Failed to send log after {max_retries + 1} attempts: {e}")
                    logger.error(f"   Log: {log_data.get('log_message', '')[:100]}...")
                    return False
        
        return False
    
    def process_message(self, log_text: str):
        """Process a single log message"""
        try:
            # Parse log entry
            log_metadata = self._parse_log_entry(log_text)
            
            # Get classification from model
            prediction = self.model_manager.predict_single(log_text)
            
            # Prepare data for API
            api_data = {
                'log_message': log_text,
                'timestamp': log_metadata['timestamp'],
                'host_ip': log_metadata['host_ip'],
                'source': log_metadata['source'],
                'log_type': log_metadata['log_type'],
                'classification_class': prediction['class'],
                'classification_name': prediction['class_name'],
                'anomaly_score': prediction['anomaly_score'],
                'severity': prediction['severity'],
                'is_anomaly': prediction['is_anomaly']
            }
            
            # Send to API (fire-and-forget with retry)
            success = self.send_to_api(api_data)
            
            if success:
                # Log success (color-coded for terminal)
                class_emoji = {
                    0: '✅',  # Normal
                    1: '🔴',  # Security
                    2: '⚠️',   # System Failure
                    3: '📊',  # Performance
                    4: '🌐',  # Network
                    5: '⚙️',   # Config
                    6: '🔧'   # Hardware
                }
                emoji = class_emoji.get(prediction['class'], '📝')
                
                logger.info(f"{emoji} {prediction['class_name']} ({prediction['severity']}) | "
                          f"Score: {prediction['anomaly_score']:.3f} | "
                          f"{log_text[:60]}...")
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            logger.error(f"   Log: {log_text[:100]}...")
    
    def start_consuming(self):
        """Start consuming messages from Kafka"""
        # Load model first
        self.load_model()
        
        logger.info(f"Starting Kafka consumer...")
        logger.info(f"Listening on topic: {self.topic}")
        logger.info(f"Sending classifications to: {self.api_url}")
        logger.info("=" * 80)
        
        try:
            consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.kafka_servers,
                value_deserializer=lambda m: m.decode('utf-8'),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='logbert_api_sender'
            )
            
            logger.info("✅ Connected to Kafka. Waiting for messages...")
            
            for message in consumer:
                log_text = message.value.strip()
                if log_text:
                    self.process_message(log_text)
                    
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down consumer...")
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
            raise
        finally:
            if 'consumer' in locals():
                consumer.close()
            logger.info("✅ Consumer stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Kafka consumer that sends log classifications to API'
    )
    parser.add_argument(
        '--api-url',
        type=str,
        default=os.getenv('API_URL', ''),
        help='PythonAnywhere API URL (e.g., https://yoursite.pythonanywhere.com)'
    )
    parser.add_argument(
        '--kafka-servers',
        type=str,
        default=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        help='Kafka bootstrap servers (default: localhost:9092)'
    )
    parser.add_argument(
        '--topic',
        type=str,
        default=os.getenv('KAFKA_TOPIC', 'log_topic'),
        help='Kafka topic name (default: log_topic)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        default=os.getenv('API_KEY', 'a44A48kPWOtCSMGF4nAWUzCpbXbdCe7iLE3lpXlbFV4'),
        help='API key for authentication (default: PythonAnywhere key)'
    )
    
    args = parser.parse_args()
    
    # Validate API URL
    if not args.api_url:
        logger.error("❌ API URL is required!")
        logger.error("   Use --api-url or set API_URL environment variable")
        logger.error("   Example: python3 kafka_consumer_api_sender.py --api-url https://logbert.pythonanywhere.com")
        sys.exit(1)
    
    # Validate URL format
    if not args.api_url.startswith(('http://', 'https://')):
        logger.error(f"❌ Invalid API URL: {args.api_url}")
        logger.error("   URL must start with http:// or https://")
        sys.exit(1)
    
    # Create and start consumer
    consumer = KafkaToAPIConsumer(
        api_url=args.api_url,
        kafka_servers=args.kafka_servers,
        topic=args.topic,
        api_key=args.api_key
    )
    
    consumer.start_consuming()


if __name__ == '__main__':
    main()
