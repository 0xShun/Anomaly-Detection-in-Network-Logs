"""
API Models for storing data received from local network.

Models:
- Alert: Anomaly alerts from LogBERT analysis
- SystemMetric: System health and performance metrics
- RawModelOutput: Raw model inference outputs for detailed analysis
"""
from django.db import models
from django.utils import timezone


class Alert(models.Model):
    """Anomaly alerts detected by LogBERT."""
    
    LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ]
    
    # Identification
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    school_id = models.CharField(max_length=100, db_index=True)
    
    # Alert details
    alert_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, db_index=True)
    anomaly_score = models.FloatField()
    affected_systems = models.JSONField(default=list)
    summary = models.TextField()
    log_count = models.IntegerField(default=0)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', db_index=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.CharField(max_length=100, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'alert_level']),
            models.Index(fields=['status', '-timestamp']),
        ]
    
    def __str__(self):
        return f"Alert {self.id}: {self.alert_level} - {self.summary[:50]}"


class SystemMetric(models.Model):
    """System health and performance metrics from local network."""
    
    # Identification
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    school_id = models.CharField(max_length=100, db_index=True)
    metric_type = models.CharField(max_length=50, db_index=True)  # e.g., 'cpu', 'memory', 'processing_time'
    
    # Metric data
    value = models.FloatField()
    unit = models.CharField(max_length=20)  # e.g., 'percent', 'seconds', 'MB'
    
    # Additional context
    metadata = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric_type', '-timestamp']),
            models.Index(fields=['school_id', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.metric_type}: {self.value}{self.unit} at {self.timestamp}"


class LogStatistic(models.Model):
    """Aggregated log processing statistics."""
    
    # Identification
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    school_id = models.CharField(max_length=100, db_index=True)
    
    # Statistics
    total_logs_processed = models.IntegerField(default=0)
    normal_logs = models.IntegerField(default=0)
    anomalous_logs = models.IntegerField(default=0)
    parsing_coverage = models.FloatField(default=0.0)  # percentage
    templates_extracted = models.IntegerField(default=0)
    
    # Processing metrics
    processing_time_seconds = models.FloatField(default=0.0)
    logs_per_second = models.FloatField(default=0.0)
    
    # Log sources breakdown
    source_breakdown = models.JSONField(default=dict)  # e.g., {"apache": 1000, "linux": 500}
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['school_id', '-timestamp']),
        ]
    
    def __str__(self):
        return f"Stats {self.school_id}: {self.total_logs_processed} logs at {self.timestamp}"


class RawModelOutput(models.Model):
    """Raw outputs from LogBERT model inference for detailed analysis."""
    
    # Identification
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    school_id = models.CharField(max_length=100, db_index=True)
    model_name = models.CharField(max_length=100)  # e.g., 'apache_full', 'linux_full'
    
    # Raw outputs
    log_sequence = models.TextField()  # The log sequence that was analyzed
    masked_predictions = models.JSONField()  # Masked token predictions
    anomaly_scores = models.JSONField()  # Per-sequence anomaly scores
    attention_weights = models.JSONField(null=True, blank=True)  # Optional attention visualization data
    
    # Classification
    is_anomaly = models.BooleanField(default=False)
    confidence_score = models.FloatField()
    
    # Context
    metadata = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['is_anomaly', '-timestamp']),
            models.Index(fields=['school_id', 'model_name', '-timestamp']),
        ]
    
    def __str__(self):
        return f"RawOutput {self.id}: {self.model_name} - {'Anomaly' if self.is_anomaly else 'Normal'}"
