from django.db import models
from django.utils import timezone


class LogEntry(models.Model):
    """Model for storing log entries from Kafka"""
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    host_ip = models.CharField(max_length=45, db_index=True)  # IPv6 compatible
    log_message = models.TextField()
    source = models.CharField(max_length=100, blank=True, db_index=True)
    log_type = models.CharField(max_length=50, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Log Entries'
        indexes = [
            models.Index(fields=['timestamp', 'log_type']),
            models.Index(fields=['host_ip', 'timestamp']),
            models.Index(fields=['source', 'timestamp']),
            models.Index(fields=['log_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.timestamp} - {self.host_ip}"


class Anomaly(models.Model):
    """Model for storing detected anomalies"""
    log_entry = models.ForeignKey(LogEntry, on_delete=models.CASCADE, related_name='anomalies')
    anomaly_score = models.FloatField(db_index=True)
    threshold = models.FloatField(default=0.5)
    is_anomaly = models.BooleanField(default=True, db_index=True)
    acknowledged = models.BooleanField(default=False, db_index=True)
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-detected_at']
        verbose_name_plural = 'Anomalies'
        indexes = [
            models.Index(fields=['detected_at', 'is_anomaly']),
            models.Index(fields=['anomaly_score', 'detected_at']),
            models.Index(fields=['acknowledged', 'detected_at']),
        ]
    
    def __str__(self):
        return f"Anomaly {self.id} - Score: {self.anomaly_score}"


class SystemStatus(models.Model):
    """Model for storing system status information"""
    service_name = models.CharField(max_length=50)  # kafka, zookeeper, consumer
    status = models.CharField(max_length=20)  # running, stopped, error
    last_check = models.DateTimeField(auto_now=True)
    details = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = 'System Statuses'
    
    def __str__(self):
        return f"{self.service_name} - {self.status}"


class PlatformSettings(models.Model):
    """Model for storing platform configuration"""
    anomaly_threshold = models.FloatField(default=0.5)
    kafka_broker_url = models.CharField(max_length=200, default='localhost:9092')
    kafka_topic_logs = models.CharField(max_length=100, default='logs')
    kafka_topic_anomalies = models.CharField(max_length=100, default='anomalies')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Platform Settings'
    
    def __str__(self):
        return f"Settings updated at {self.updated_at}"
