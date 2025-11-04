"""Admin configuration for API models."""
from django.contrib import admin
from .models import Alert, SystemMetric, LogStatistic, RawModelOutput


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """Admin interface for Alert model."""
    list_display = ['id', 'timestamp', 'school_id', 'alert_level', 'anomaly_score', 'status', 'log_count']
    list_filter = ['alert_level', 'status', 'school_id', 'timestamp']
    search_fields = ['summary', 'school_id', 'affected_systems']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Identification', {
            'fields': ('timestamp', 'school_id')
        }),
        ('Alert Details', {
            'fields': ('alert_level', 'anomaly_score', 'affected_systems', 'summary', 'log_count')
        }),
        ('Status Tracking', {
            'fields': ('status', 'acknowledged_at', 'acknowledged_by', 'resolution_notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    """Admin interface for SystemMetric model."""
    list_display = ['id', 'timestamp', 'school_id', 'metric_type', 'value', 'unit']
    list_filter = ['metric_type', 'school_id', 'timestamp']
    search_fields = ['metric_type', 'school_id']
    date_hierarchy = 'timestamp'


@admin.register(LogStatistic)
class LogStatisticAdmin(admin.ModelAdmin):
    """Admin interface for LogStatistic model."""
    list_display = ['id', 'timestamp', 'school_id', 'total_logs_processed', 'anomalous_logs', 'parsing_coverage']
    list_filter = ['school_id', 'timestamp']
    search_fields = ['school_id']
    date_hierarchy = 'timestamp'


@admin.register(RawModelOutput)
class RawModelOutputAdmin(admin.ModelAdmin):
    """Admin interface for RawModelOutput model."""
    list_display = ['id', 'timestamp', 'school_id', 'model_name', 'is_anomaly', 'confidence_score']
    list_filter = ['is_anomaly', 'model_name', 'school_id', 'timestamp']
    search_fields = ['school_id', 'model_name', 'log_sequence']
    readonly_fields = ['created_at']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Identification', {
            'fields': ('timestamp', 'school_id', 'model_name')
        }),
        ('Model Output', {
            'fields': ('log_sequence', 'masked_predictions', 'anomaly_scores', 'attention_weights')
        }),
        ('Classification', {
            'fields': ('is_anomaly', 'confidence_score')
        }),
        ('Context', {
            'fields': ('metadata',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
