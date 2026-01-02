import json
import torch
import pickle
import re
import hashlib
from kafka import KafkaConsumer
from collections import deque
from statistics import mean
from datetime import datetime
from dateutil import parser as date_parser
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import LogEntry, Anomaly, SystemStatus
from .ml_utils import HybridBERTModelManager

class DashboardConsumer(AsyncWebsocketConsumer):
    # Kafka configuration
    KAFKA_TOPIC = "log_topic"
    KAFKA_SERVER = "localhost:9092"
    
    # Runtime configuration
    METRICS_WINDOW_SIZE = 1000  # Number of records to track for dynamic thresholds
    THRESHOLD_RECOMPUTE_INTERVAL = 300  # Seconds between threshold recalculations

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_manager = None
        self.kafka_consumer = None
        self.ANOMALY_THRESHOLD = 0.5  # Default threshold for anomaly detection
        self.normal_scores = deque(maxlen=self.METRICS_WINDOW_SIZE)
        self.abnormal_scores = deque(maxlen=self.METRICS_WINDOW_SIZE)
        self.score_history = []
        self.last_threshold_update = None
        # Track classification statistics
        self.classification_counts = {i: 0 for i in range(7)}
        # Hostname to IP mapping (consistent IP assignment per hostname)
        self.hostname_ip_map = {}

    async def connect(self):
        # Initialize ML components and load threshold
        await database_sync_to_async(self._init_ml_components)()
        
        # Accept connection and start Kafka consumer
        await self.accept()
        await self.channel_layer.group_add("dashboard", self.channel_name)
        
        # Start Kafka consumer in background thread
        import threading
        kafka_thread = threading.Thread(target=self._start_kafka_consumer)
        kafka_thread.daemon = True
        kafka_thread.start()
    
        async def disconnect(self, close_code):
            await self.channel_layer.group_discard("dashboard", self.channel_name)

        async def receive_json(self, content):
            """Handle admin commands from frontend"""
            command = content.get("command")
            if command == "override_threshold":
                new_threshold = content.get("value")
                if new_threshold is not None and 0 <= new_threshold <= 1.0:
                    self.ANOMALY_THRESHOLD = float(new_threshold)
                    self._persist_current_threshold()
                    await self.send_json({"status": "success", "message": "Threshold updated.", "current_threshold": self.ANOMALY_THRESHOLD})
                else:
                    await self.send_json({"status": "error", "message": "Invalid threshold value."})
            elif command == "acknowledge_anomaly":
                anomaly_id = content.get("anomaly_id")
                await database_sync_to_async(self._acknowledge_anomaly)(anomaly_id)
                await self.send_json({"status": "success", "message": "Anomaly acknowledged."})
            elif command == "update_system_status":
                status = content.get("status")
                await database_sync_to_async(self._update_system_status)(status)
                await self.send_json({"status": "success", "message": "System status updated."})
            elif command == "get_metrics":
                metrics = self._get_metrics()
                await self.send_json({"status": "success", "metrics": metrics})
            else:
                await self.send_json({"status": "error", "message": "Unknown command."})

        def _acknowledge_anomaly(self, anomaly_id):
            try:
                anomaly = Anomaly.objects.get(id=anomaly_id)
                anomaly.acknowledged = True
                anomaly.save()
            except Exception as e:
                print(f"Acknowledge anomaly error: {str(e)}")

        def _update_system_status(self, status):
            try:
                sys_status, _ = SystemStatus.objects.get_or_create(id=1)
                sys_status.status = status
                sys_status.save()
            except Exception as e:
                print(f"System status update error: {str(e)}")

        def _get_metrics(self):
            # Return metrics for review
            try:
                normal_scores = list(self.normal_scores)
                abnormal_scores = list(self.abnormal_scores)
                threshold = self.ANOMALY_THRESHOLD
                FP = sum(1 for s in normal_scores if s > threshold)
                TP = sum(1 for s in abnormal_scores if s > threshold)
                TN = len(normal_scores) - FP
                FN = len(abnormal_scores) - TP
                precision = TP / (TP + FP) if (TP + FP) > 0 else 0
                recall = TP / (TP + FN) if (TP + FN) > 0 else 0
                f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                return {
                    "current_threshold": round(threshold, 4),
                    "normal_mean": round(mean(normal_scores), 4) if normal_scores else 0,
                    "abnormal_mean": round(mean(abnormal_scores), 4) if abnormal_scores else 0,
                    "precision": round(precision, 4),
                    "recall": round(recall, 4),
                    "f1_score": round(f1_score, 4),
                    "TP": TP,
                    "FP": FP,
                    "TN": TN,
                    "FN": FN
                }
            except Exception as e:
                print(f"Metrics error: {str(e)}")

    def _init_ml_components(self):
        """Initialize Hybrid-BERT model manager"""
        try:
            print("🔧 Initializing Hybrid-BERT Model Manager for WebSocket consumer...")
            self.model_manager = HybridBERTModelManager()
            
            if not self.model_manager.is_loaded():
                raise RuntimeError("Hybrid-BERT models failed to load")
            
            print("✅ Hybrid-BERT Model Manager initialized successfully")
            self.last_threshold_update = datetime.now()
            
        except Exception as e:
            error_msg = f"ML Component initialization failed: {str(e)}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

    def _load_precomputed_threshold(self):
        """Deprecated - threshold is now dynamically calculated"""
        pass  # Keeping for compatibility

    def _start_kafka_consumer(self):
        """Initialize Kafka consumer and start polling"""
        try:
            self.kafka_consumer = KafkaConsumer(
                self.KAFKA_TOPIC,
                bootstrap_servers=self.KAFKA_SERVER,
                auto_offset_reset='latest',
                enable_auto_commit=False
            )
            for message in self.kafka_consumer:
                self._process_message(message.value.decode('utf-8'))
        except Exception as e:
            print(f"Kafka Connection Error: {str(e)}")

    def _process_message(self, raw_message):
        """Parse log message, analyze with Hybrid-BERT, and send results"""
        try:
            # Enhanced parsing with log source detection
            parsed_data = self._parse_log_entry(raw_message)
            
            # Use Hybrid-BERT for prediction
            prediction = self.model_manager.predict_single(parsed_data['message_content'])
            
            # Extract prediction details
            anomaly_score = prediction['anomaly_score']
            predicted_class = prediction['class']
            class_name = prediction['class_name']
            is_anomaly = prediction['is_anomaly']
            severity = prediction['severity']
            
            # Update classification statistics
            self.classification_counts[predicted_class] += 1

            # Update threshold if needed
            current_time = datetime.now()
            if (self.last_threshold_update is None or 
                (current_time - self.last_threshold_update).total_seconds() > self.THRESHOLD_RECOMPUTE_INTERVAL):
                self._update_dynamic_threshold()
                self.last_threshold_update = current_time
            
            # Track scores based on anomaly status
            if is_anomaly:
                self.abnormal_scores.append(anomaly_score)
            else:
                self.normal_scores.append(anomaly_score)
                
            # Store to database with all parsed fields
            log_entry = LogEntry.objects.create(
                timestamp=parsed_data['timestamp'],
                host_ip=parsed_data['host_ip'],
                log_type=parsed_data['log_type'],
                log_message=parsed_data['message_content'],
                source=parsed_data['source'],
            )
            
            # Create anomaly record if detected (or always create for all logs with classification)
            Anomaly.objects.create(
                log_entry=log_entry,
                anomaly_score=anomaly_score,
                threshold=self.ANOMALY_THRESHOLD,
                is_anomaly=is_anomaly,
                acknowledged=False,
                classification_class=predicted_class,
                classification_name=class_name,
                severity=severity
            )
            
            # Send to WebSocket
            self.channel_layer.group_send(
                "dashboard",
                {
                    "type": "dashboard_update",
                    "data": self._format_response(
                        log_entry, 
                        prediction,
                        anomaly_score,
                        is_anomaly
                    )
                }
            )
            
        except Exception as e:
            print(f"Message Processing Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _parse_log_entry(self, raw_message):
        """
        Enhanced log parsing with source detection, IP extraction, timestamp parsing, and log type detection.
        
        Returns dict with: timestamp, host_ip, log_type, message_content, source
        """
        # Detect log source (Apache vs Linux/syslog)
        log_source = self._detect_log_source(raw_message)
        
        if log_source == 'apache':
            return self._parse_apache_log(raw_message)
        elif log_source == 'linux':
            return self._parse_linux_log(raw_message)
        else:
            return self._parse_generic_log(raw_message)
    
    def _detect_log_source(self, log_line):
        """Detect if log is from Apache or Linux/syslog"""
        # Apache logs typically start with [Day Month DD HH:MM:SS YYYY]
        if re.match(r'^\[[\w\s:]+\d{4}\]', log_line):
            return 'apache'
        # Linux syslog format: Month DD HH:MM:SS hostname
        elif re.match(r'^[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\w+', log_line):
            return 'linux'
        else:
            return 'generic'
    
    def _parse_apache_log(self, log_line):
        """Parse Apache HTTP server log format"""
        # Apache format: [Thu Jun 09 06:07:04 2005] [error] message
        timestamp_match = re.match(r'^\[([^\]]+)\]', log_line)
        level_match = re.search(r'\]\s*\[(\w+)\]', log_line)
        
        # Extract timestamp
        if timestamp_match:
            try:
                timestamp = date_parser.parse(timestamp_match.group(1))
            except:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        # Extract log level
        log_type = level_match.group(1) if level_match else 'info'
        
        # Extract message (everything after second ])
        message_start = log_line.find(']', log_line.find(']') + 1) + 1
        message_content = log_line[message_start:].strip() if message_start > 0 else log_line
        
        # Extract IP from message or generate contextual one
        host_ip = self._extract_ip(message_content, 'apache')
        
        return {
            'timestamp': timestamp,
            'host_ip': host_ip,
            'log_type': log_type,
            'message_content': message_content,
            'source': 'apache'
        }
    
    def _parse_linux_log(self, log_line):
        """Parse Linux syslog format"""
        # Linux format: Jun  9 06:06:20 combo syslogd 1.4.1: restart.
        parts = log_line.split()
        
        # Extract timestamp (Month Day HH:MM:SS)
        if len(parts) >= 3:
            try:
                timestamp_str = f"{parts[0]} {parts[1]} {parts[2]}"
                # Parse with current year since logs don't include it
                timestamp = date_parser.parse(timestamp_str)
                # Keep the year from original data (will be current year from parser)
            except:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        # Extract hostname (4th element)
        hostname = parts[3] if len(parts) > 3 else 'localhost'
        
        # Extract process/service (5th element, before colon)
        if len(parts) > 4:
            service = parts[4].rstrip(':')
            # Use service as log type category
            log_type = self._map_service_to_log_type(service)
        else:
            service = 'system'
            log_type = 'info'
        
        # Message is everything after hostname and service
        message_content = ' '.join(parts[4:]) if len(parts) > 4 else log_line
        
        # Get or generate IP for this hostname
        host_ip = self._get_ip_for_hostname(hostname)
        
        return {
            'timestamp': timestamp,
            'host_ip': host_ip,
            'log_type': log_type,
            'message_content': message_content,
            'source': hostname
        }
    
    def _parse_generic_log(self, log_line):
        """Fallback parser for unknown log formats"""
        # Try to extract timestamp from anywhere in the line
        timestamp = datetime.now()
        
        # Try to extract IP
        host_ip = self._extract_ip(log_line, 'generic')
        
        # Use simple split as fallback
        components = log_line.strip().split()
        log_type = components[1] if len(components) > 1 else 'info'
        message_content = log_line
        
        return {
            'timestamp': timestamp,
            'host_ip': host_ip,
            'log_type': log_type,
            'message_content': message_content,
            'source': 'unknown'
        }
    
    def _extract_ip(self, message, context='generic'):
        """
        Extract IP address from log message.
        If no IP found, generate contextual IP based on context.
        """
        # Try to find IPv4 address in message
        ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ip_match = re.search(ipv4_pattern, message)
        
        if ip_match:
            return ip_match.group(0)
        
        # No IP found - generate contextual IP
        if context == 'apache':
            # Apache web servers - use 10.0.x.x range
            return '10.0.0.5'
        elif 'security' in message.lower() or 'auth' in message.lower():
            # Security events - external IP range
            return f"203.0.113.{hash(message) % 256}"
        elif 'network' in message.lower() or 'connection' in message.lower():
            # Network events
            return f"192.168.1.{hash(message) % 256}"
        else:
            # Default internal range
            return '192.168.1.10'
    
    def _get_ip_for_hostname(self, hostname):
        """
        Get consistent IP for a hostname using hash-based mapping.
        Same hostname always gets same IP.
        """
        if hostname in self.hostname_ip_map:
            return self.hostname_ip_map[hostname]
        
        # Generate consistent IP from hostname hash
        hash_value = int(hashlib.md5(hostname.encode()).hexdigest(), 16)
        ip_suffix = (hash_value % 240) + 10  # Range: 10-250
        generated_ip = f"192.168.1.{ip_suffix}"
        
        self.hostname_ip_map[hostname] = generated_ip
        return generated_ip
    
    def _map_service_to_log_type(self, service):
        """Map Linux service/process name to log type"""
        service_lower = service.lower()
        
        if 'kernel' in service_lower:
            return 'kernel'
        elif any(x in service_lower for x in ['error', 'fail', 'crit']):
            return 'error'
        elif any(x in service_lower for x in ['warn']):
            return 'warning'
        elif any(x in service_lower for x in ['syslog', 'auth', 'sudo']):
            return 'auth'
        else:
            return 'info'
            
    def _update_dynamic_threshold(self):
        """Update threshold based on recent data using methodology from predict_log.py"""
        if not self.abnormal_scores or not self.normal_scores:
            return
            
        # Use the last N results (windowed)
        test_abnormal_results = list(self.abnormal_scores)
        test_normal_results = list(self.normal_scores)
        
        # Create parameters similar to training
        params = {
            'num_candidate_vectors': len(test_abnormal_results) + len(test_normal_results),
            'window_size': 10,
        }
        
        # Generate thresholds to test
        seq_range = [
            self.ANOMALY_THRESHOLD - 0.2,
            self.ANOMALY_THRESHOLD - 0.1,
            self.ANOMALY_THRESHOLD,
            self.ANOMALY_THRESHOLD + 0.1,
            self.ANOMALY_THRESHOLD + 0.2
        ]
        
        # Find optimal threshold
        best_threshold = self._find_best_threshold(
            test_normal_results, test_abnormal_results, params, seq_range
        )
        
        if best_threshold:  # Only update if we found a valid threshold
            self.ANOMALY_THRESHOLD = best_threshold

    def _find_best_threshold(self, test_normal_results, test_abnormal_results, params, seq_range):
        """Implementation adapted from predict_log.py"""
        best_result = None
        best_threshold = None
        
        # Filter out invalid ranges
        valid_seq_range = [th for th in seq_range if 0 <= th <= 1.0]
        
        for seq_th in sorted(valid_seq_range):
            # Calculate TP/FP based on current sequence threshold
            FP = sum(1 for s in test_normal_results if s > seq_th)
            TP = sum(1 for s in test_abnormal_results if s > seq_th)
            
            if TP == 0:
                continue  # Skip thresholds that don't detect any anomalies
                
            TN = len(test_normal_results) - FP
            FN = len(test_abnormal_results) - TP
            
            try:
                # Calculate metrics
                precision = 100 * TP / (TP + FP)
                recall = 100 * TP / (TP + FN)
                f1_score = 2 * precision * recall / (precision + recall)
                
                # Update best result
                if best_result is None or f1_score > best_result[-1]:
                    best_result = [seq_th, FP, TP, TN, FN, precision, recall, f1_score]
                    best_threshold = seq_th
            except ZeroDivisionError:
                continue  # Skip this threshold if there's division by zero
                
        return best_threshold

    def _persist_current_threshold(self):
        """Deprecated - no longer persisting threshold to file"""
        pass  # Keeping for compatibility
            
    def _format_response(self, log_entry, prediction, anomaly_score, is_anomaly):
        """Format WebSocket message with detailed metrics and classification"""
        return {
            "id": log_entry.id,
            "timestamp": str(log_entry.timestamp),
            "log_type": log_entry.log_type,
            "message": log_entry.log_message,
            "is_anomaly": is_anomaly,
            "anomaly_score": round(anomaly_score, 4),
            "classification": {
                "class": prediction['class'],
                "class_name": prediction['class_name'],
                "severity": prediction['severity'],
                "probabilities": [round(p, 4) for p in prediction['probabilities']]
            },
            "current_threshold": round(self.ANOMALY_THRESHOLD, 4),
            "normal_mean": round(mean(self.normal_scores), 4) if self.normal_scores else 0,
            "abnormal_mean": round(mean(self.abnormal_scores), 4) if self.abnormal_scores else 0,
            "classification_stats": self.classification_counts
        }