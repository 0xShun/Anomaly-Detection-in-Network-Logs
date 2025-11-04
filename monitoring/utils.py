import socket
import subprocess
import psutil
from django.conf import settings
from kafka import KafkaAdminClient, KafkaConsumer
from kafka.errors import KafkaError
import logging

logger = logging.getLogger(__name__)


def check_kafka_status():
    """Check Kafka broker status"""
    try:
        # Try to connect to Kafka broker
        admin_client = KafkaAdminClient(
            bootstrap_servers=[settings.KAFKA_BROKER_URL],
            request_timeout_ms=5000
        )
        admin_client.list_topics()
        admin_client.close()
        return {
            'status': 'running',
            'details': 'Kafka broker is accessible'
        }
    except KafkaError as e:
        return {
            'status': 'error',
            'details': f'Kafka connection failed: {str(e)}'
        }
    except Exception as e:
        return {
            'status': 'stopped',
            'details': f'Kafka check failed: {str(e)}'
        }


def check_zookeeper_status():
    """Check Zookeeper status"""
    try:
        # Try to connect to Zookeeper on port 2181
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 2181))
        sock.close()
        
        if result == 0:
            return {
                'status': 'running',
                'details': 'Zookeeper is accessible on port 2181'
            }
        else:
            return {
                'status': 'stopped',
                'details': 'Zookeeper is not accessible on port 2181'
            }
    except Exception as e:
        return {
            'status': 'error',
            'details': f'Zookeeper check failed: {str(e)}'
        }


def check_consumer_status():
    """Check consumer process status"""
    try:
        # Look for Python processes that might be running the consumer
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any('consumer' in arg.lower() for arg in cmdline):
                    return {
                        'status': 'running',
                        'details': f'Consumer process found (PID: {proc.info["pid"]})'
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            'status': 'stopped',
            'details': 'No consumer process found'
        }
    except Exception as e:
        return {
            'status': 'error',
            'details': f'Consumer check failed: {str(e)}'
        }


def get_system_status():
    """Get overall system status"""
    kafka_status = check_kafka_status()
    zookeeper_status = check_zookeeper_status()
    consumer_status = check_consumer_status()
    
    # Determine overall status
    all_running = all(
        status['status'] == 'running' 
        for status in [kafka_status, zookeeper_status, consumer_status]
    )
    
    any_error = any(
        status['status'] == 'error' 
        for status in [kafka_status, zookeeper_status, consumer_status]
    )
    
    if all_running:
        overall_status = 'running'
    elif any_error:
        overall_status = 'error'
    else:
        overall_status = 'stopped'
    
    return {
        'overall': overall_status,
        'kafka': kafka_status,
        'zookeeper': zookeeper_status,
        'consumer': consumer_status,
    }


def get_kafka_consumer():
    """Get Kafka consumer instance"""
    try:
        consumer = KafkaConsumer(
            settings.KAFKA_TOPIC_ANOMALIES,
            bootstrap_servers=[settings.KAFKA_BROKER_URL],
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='webplatform_consumer',
            value_deserializer=lambda x: x.decode('utf-8')
        )
        return consumer
    except Exception as e:
        logger.error(f"Failed to create Kafka consumer: {e}")
        return None


def get_kafka_producer():
    """Get Kafka producer instance"""
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=[settings.KAFKA_BROKER_URL],
            value_serializer=lambda x: x.encode('utf-8')
        )
        return producer
    except Exception as e:
        logger.error(f"Failed to create Kafka producer: {e}")
        return None 