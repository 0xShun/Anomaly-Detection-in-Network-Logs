"""Serializers for API data models."""
from rest_framework import serializers
from .models import Alert, SystemMetric, LogStatistic, RawModelOutput


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for Alert model."""
    
    class Meta:
        model = Alert
        fields = [
            'id', 'timestamp', 'school_id', 'alert_level', 'anomaly_score',
            'affected_systems', 'summary', 'log_count', 'status',
            'acknowledged_at', 'acknowledged_by', 'resolution_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SystemMetricSerializer(serializers.ModelSerializer):
    """Serializer for SystemMetric model."""
    
    class Meta:
        model = SystemMetric
        fields = [
            'id', 'timestamp', 'school_id', 'metric_type', 'value', 'unit',
            'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class LogStatisticSerializer(serializers.ModelSerializer):
    """Serializer for LogStatistic model."""
    
    class Meta:
        model = LogStatistic
        fields = [
            'id', 'timestamp', 'school_id', 'total_logs_processed',
            'normal_logs', 'anomalous_logs', 'parsing_coverage',
            'templates_extracted', 'processing_time_seconds',
            'logs_per_second', 'source_breakdown', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RawModelOutputSerializer(serializers.ModelSerializer):
    """Serializer for RawModelOutput model."""
    
    class Meta:
        model = RawModelOutput
        fields = [
            'id', 'timestamp', 'school_id', 'model_name', 'log_sequence',
            'masked_predictions', 'anomaly_scores', 'attention_weights',
            'is_anomaly', 'confidence_score', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
