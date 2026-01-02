from django.contrib import admin
from .models import LogEntry, Anomaly, SystemStatus, PlatformSettings, ThreatIntelligenceCache

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
	list_display = ('id', 'timestamp', 'host_ip', 'log_type')

@admin.register(Anomaly)
class AnomalyAdmin(admin.ModelAdmin):
	list_display = ('id', 'log_entry', 'anomaly_score', 'threshold', 'is_anomaly', 'acknowledged', 'detected_at')

@admin.register(SystemStatus)
class SystemStatusAdmin(admin.ModelAdmin):
	list_display = ('id', 'service_name', 'status', 'last_check')

@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
	list_display = ('id', 'anomaly_threshold', 'kafka_broker_url', 'updated_at')

@admin.register(ThreatIntelligenceCache)
class ThreatIntelligenceCacheAdmin(admin.ModelAdmin):
	list_display = ('ip_address', 'vt_malicious', 'abuseipdb_confidence_score', 'updated_at')
	search_fields = ('ip_address',)
	list_filter = ('updated_at', 'vt_queried_at', 'abuseipdb_queried_at', 'shodan_queried_at')
	readonly_fields = ('created_at', 'updated_at')

