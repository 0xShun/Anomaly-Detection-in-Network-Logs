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
    """Model for storing detected anomalies with classification details"""
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    log_entry = models.ForeignKey(LogEntry, on_delete=models.CASCADE, related_name='anomalies')
    anomaly_score = models.FloatField(db_index=True)
    threshold = models.FloatField(default=0.5)
    is_anomaly = models.BooleanField(default=True, db_index=True)
    acknowledged = models.BooleanField(default=False, db_index=True)
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Classification fields from Hybrid-BERT model
    classification_class = models.IntegerField(null=True, blank=True, db_index=True, 
                                               help_text="Class number (0-6): 0=Normal, 1=Security, 2=System Failure, 3=Performance, 4=Network, 5=Config, 6=Hardware")
    classification_name = models.CharField(max_length=50, null=True, blank=True, db_index=True,
                                          help_text="Human-readable class name (e.g., 'Security Anomaly')")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, null=True, blank=True, db_index=True,
                               help_text="Severity level: info, medium, high, critical")
    
    class Meta:
        ordering = ['-detected_at']
        verbose_name_plural = 'Anomalies'
        indexes = [
            models.Index(fields=['detected_at', 'is_anomaly']),
            models.Index(fields=['anomaly_score', 'detected_at']),
            models.Index(fields=['acknowledged', 'detected_at']),
            models.Index(fields=['classification_class', 'detected_at']),
            models.Index(fields=['severity', 'detected_at']),
        ]
    
    def __str__(self):
        return f"Anomaly {self.id} - {self.classification_name or 'Unknown'} - Score: {self.anomaly_score}"


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


class ThreatIntelligenceCache(models.Model):
    """Cache for threat intelligence API results to avoid hitting rate limits"""
    ip_address = models.CharField(max_length=45, unique=True, db_index=True)
    
    # VirusTotal data
    vt_malicious = models.IntegerField(null=True, blank=True)
    vt_suspicious = models.IntegerField(null=True, blank=True)
    vt_harmless = models.IntegerField(null=True, blank=True)
    vt_undetected = models.IntegerField(null=True, blank=True)
    vt_reputation = models.IntegerField(null=True, blank=True)
    vt_country = models.CharField(max_length=100, null=True, blank=True)
    vt_asn = models.CharField(max_length=100, null=True, blank=True)
    vt_as_owner = models.CharField(max_length=255, null=True, blank=True)
    vt_last_analysis_date = models.CharField(max_length=100, null=True, blank=True)
    vt_flagged_engines = models.JSONField(null=True, blank=True)
    vt_queried_at = models.DateTimeField(null=True, blank=True)
    
    # AbuseIPDB data
    abuseipdb_confidence_score = models.IntegerField(null=True, blank=True)
    abuseipdb_total_reports = models.IntegerField(null=True, blank=True)
    abuseipdb_num_distinct_users = models.IntegerField(null=True, blank=True)
    abuseipdb_country = models.CharField(max_length=100, null=True, blank=True)
    abuseipdb_isp = models.CharField(max_length=255, null=True, blank=True)
    abuseipdb_usage_type = models.CharField(max_length=100, null=True, blank=True)
    abuseipdb_categories = models.JSONField(null=True, blank=True)
    abuseipdb_is_whitelisted = models.BooleanField(default=False)
    abuseipdb_last_reported_at = models.CharField(max_length=100, null=True, blank=True)
    abuseipdb_queried_at = models.DateTimeField(null=True, blank=True)
    
    # Shodan data
    shodan_hostnames = models.JSONField(null=True, blank=True)
    shodan_domains = models.JSONField(null=True, blank=True)
    shodan_ports = models.JSONField(null=True, blank=True)
    shodan_vulns = models.JSONField(null=True, blank=True)
    shodan_cpes = models.JSONField(null=True, blank=True)
    shodan_organization = models.CharField(max_length=255, null=True, blank=True)
    shodan_os = models.CharField(max_length=100, null=True, blank=True)
    shodan_country = models.CharField(max_length=100, null=True, blank=True)
    shodan_city = models.CharField(max_length=100, null=True, blank=True)
    shodan_isp = models.CharField(max_length=255, null=True, blank=True)
    shodan_tags = models.JSONField(null=True, blank=True)
    shodan_last_update = models.CharField(max_length=100, null=True, blank=True)
    shodan_queried_at = models.DateTimeField(null=True, blank=True)
    
    # Cache metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Threat Intelligence Cache'
        verbose_name_plural = 'Threat Intelligence Cache'
        indexes = [
            models.Index(fields=['ip_address', 'updated_at']),
        ]
    
    def __str__(self):
        return f"Threat Intel Cache: {self.ip_address}"
    
    def is_expired(self, days=7):
        """Check if cache is older than specified days (default 7)"""
        from datetime import timedelta
        if not self.updated_at:
            return True
        expiry_date = timezone.now() - timedelta(days=days)
        return self.updated_at < expiry_date
    
    def get_summary(self):
        """Get a summary of threat intelligence data"""
        threats = []
        if self.vt_malicious and self.vt_malicious > 0:
            threats.append(f"VirusTotal: {self.vt_malicious} malicious detections")
        if self.abuseipdb_confidence_score and self.abuseipdb_confidence_score > 50:
            threats.append(f"AbuseIPDB: {self.abuseipdb_confidence_score}% confidence")
        if self.shodan_vulns and len(self.shodan_vulns) > 0:
            threats.append(f"Shodan: {len(self.shodan_vulns)} vulnerabilities")
        return threats if threats else ["No significant threats detected"]
