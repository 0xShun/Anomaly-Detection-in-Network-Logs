import json
import torch
import pickle
from kafka import KafkaConsumer
from collections import deque
from statistics import mean
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import LogEntry, Anomaly, SystemStatus
from bert_pytorch.model.bert import BERTModel
from transformers import BertTokenizer

class DashboardConsumer(AsyncWebsocketConsumer):
    # Model and Kafka configuration
    MODEL_PATH = "../output/university_logs/bert/best_bert.pth"
    VOCAB_PATH = "../output/university_logs/vocab.pkl"
    THRESHOLD_PATH = "../output/university_logs/bert_threshold.pkl"
    KAFKA_TOPIC = "log_topic"
    KAFKA_SERVER = "localhost:9092"
    
    # Runtime configuration
    METRICS_WINDOW_SIZE = 1000  # Number of records to track for dynamic thresholds
    THRESHOLD_RECOMPUTE_INTERVAL = 300  # Seconds between threshold recalculations

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = None
        self.tokenizer = None
        self.kafka_consumer = None
        self.ANOMALY_THRESHOLD = 0.5  # Will be updated during initialization
        self.normal_scores = deque(maxlen=self.METRICS_WINDOW_SIZE)
        self.abnormal_scores = deque(maxlen=self.METRICS_WINDOW_SIZE)
        self.score_history = []
        self.last_threshold_update = None

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
        """Load BERT model, vocab, and optimal threshold"""
        try:
            # Initialize BERT tokenizer
            self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
            
            # Load vocab
            vocab_size = len(pickle.load(open(self.VOCAB_PATH, "rb")))
            
            # Initialize BERT model
            self.model = BERTModel(vocab_size=vocab_size)
            
            # Load trained weights
            state_dict = torch.load(self.MODEL_PATH, map_location=torch.device('cpu'))
            self.model.load_state_dict(state_dict)
            self.model.eval()
            
            # Load threshold
            self._load_precomputed_threshold()
            self.last_threshold_update = datetime.now()
            
        except Exception as e:
            print(f"ML Component Load Error: {str(e)}")

    def _load_precomputed_threshold(self):
        """Load threshold determined during model evaluation"""
        try:
            with open(self.THRESHOLD_PATH, 'rb') as f:
                self.ANOMALY_THRESHOLD = pickle.load(f)
        except (FileNotFoundError, pickle.PickleError):
            pass  # Use default if not available

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
        """Parse log message, analyze, and send results"""
        try:
            # Mini parser - simple split example
            components = raw_message.strip().split()
            timestamp = components[0] if len(components) > 0 else ""
            level = components[1] if len(components) > 1 else ""
            message_content = " ".join(components[2:]) if len(components) > 2 else ""
            
            # Tokenize and get model output
            inputs = self.tokenizer(
                message_content, 
                return_tensors="pt", 
                padding=True, 
                truncation=True
            )
            
            with torch.no_grad():
                outputs = self.model(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs['attention_mask']
                )
                
                # Convert model output to anomaly score
                anomaly_score = torch.sigmoid(outputs.logits[:, 0]).item()  # Use first token's prediction

            # Update threshold if needed
            current_time = datetime.now()
            if (self.last_threshold_update is None or 
                (current_time - self.last_threshold_update).total_seconds() > self.THRESHOLD_RECOMPUTE_INTERVAL):
                self._update_dynamic_threshold()
                self._persist_current_threshold()
                self.last_threshold_update = current_time
            
            # Track scores based on anomaly status
            is_anomaly = anomaly_score > self.ANOMALY_THRESHOLD
            if is_anomaly:
                self.abnormal_scores.append(anomaly_score)
            else:
                self.normal_scores.append(anomaly_score)
                
            # Store to database
            log_entry = LogEntry.objects.create(
                timestamp=timestamp,
                level=level,
                message=message_content,
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score
            )
            
            # Send to WebSocket
            self.channel_layer.group_send(
                "dashboard",
                {
                    "type": "dashboard_update",
                    "data": self._format_response(log_entry)
                }
            )
            
        except Exception as e:
            print(f"Message Processing Error: {str(e)}")
            
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
        """Save updated threshold for future use"""
        try:
            with open(self.THRESHOLD_PATH, 'wb') as f:
                pickle.dump(self.ANOMALY_THRESHOLD, f)
            return True
        except Exception as e:
            print(f"Threshold persistence failed: {str(e)}")
            return False
            
    def _format_response(self, log_entry):
        """Format WebSocket message with detailed metrics"""
        return {
            "id": log_entry.id,
            "timestamp": str(log_entry.timestamp),
            "level": log_entry.level,
            "message": log_entry.message,
            "is_anomaly": log_entry.is_anomaly,
            "anomaly_score": round(log_entry.anomaly_score, 4),
            "current_threshold": round(self.ANOMALY_THRESHOLD, 4),
            "normal_mean": round(mean(self.normal_scores), 4) if self.normal_scores else 0,
            "abnormal_mean": round(mean(self.abnormal_scores), 4) if self.abnormal_scores else 0
        }