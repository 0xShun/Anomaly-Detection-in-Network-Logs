from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from dashboard.models import LogEntry, Anomaly, SystemStatus, PlatformSettings
from authentication.models import AdminUser


class Command(BaseCommand):
    help = 'Populate database with sample data for demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before adding sample data',
        )
        parser.add_argument(
            '--streamlit',
            action='store_true',
            help='Create additional data optimized for Streamlit visualization',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            LogEntry.objects.all().delete()
            Anomaly.objects.all().delete()
            SystemStatus.objects.all().delete()
            PlatformSettings.objects.all().delete()

        self.stdout.write('Creating sample data...')

        # Create sample log entries
        self.create_sample_logs()
        
        # Create sample anomalies
        self.create_sample_anomalies()
        
        # Create system status entries
        self.create_system_status()
        
        # Create platform settings
        self.create_platform_settings()

        # Create additional data for Streamlit if requested
        if options['streamlit']:
            self.create_streamlit_optimized_data()

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )

    def create_sample_logs(self):
        """Create sample log entries"""
        hosts = ['192.168.1.100', '192.168.1.101', '192.168.1.102', '10.0.0.50', '172.16.0.25', 
                '203.0.113.10', '198.51.100.20', '203.0.113.30', '192.168.2.100', '10.0.1.50']
        sources = ['web_server', 'database', 'firewall', 'load_balancer', 'application', 
                  'api_gateway', 'cache_server', 'monitoring_agent', 'backup_service', 'security_scanner']
        log_types = ['error', 'warning', 'info', 'debug']
        
        # Sample log messages with more variety
        log_messages = [
            "Connection timeout after 30 seconds",
            "Database connection established successfully",
            "Invalid login attempt from IP 203.0.113.45",
            "Server started on port 8080",
            "Memory usage at 85% - warning threshold exceeded",
            "Backup completed successfully",
            "SSL certificate expired - renewal required",
            "User authentication failed - invalid credentials",
            "System reboot initiated by administrator",
            "Network interface eth0 is down",
            "Disk space usage: 92% - critical level",
            "Application deployed successfully to production",
            "Firewall rule updated - port 22 access restricted",
            "Load balancer health check failed for server-02",
            "Database query executed in 2.3 seconds",
            "Security scan completed - 3 vulnerabilities found",
            "Backup verification failed - integrity check error",
            "Service restarted due to memory leak",
            "SSL handshake failed - certificate mismatch",
            "User session expired - automatic logout",
            "System resources optimized - performance improved",
            "Network packet loss detected - 5% loss rate",
            "Application error: NullPointerException in UserService",
            "Database connection pool exhausted",
            "Firewall blocked suspicious traffic from 198.51.100.0/24",
            "API rate limit exceeded for user 12345",
            "Cache miss - data fetched from database",
            "Health check failed - service unresponsive",
            "Configuration file updated successfully",
            "Log rotation completed - old files archived",
            "Performance alert: Response time > 2 seconds",
            "Security alert: Multiple failed login attempts",
            "Backup job started - estimated completion in 30 minutes",
            "Service discovery: New instance registered",
            "Load balancing: Traffic redirected to healthy node",
            "Monitoring: CPU usage spike detected",
            "Authentication: JWT token expired",
            "Network: DNS resolution failed",
            "Storage: Disk I/O bottleneck detected",
            "Application: Memory leak detected in service",
            "Security: Brute force attack detected",
            "Database: Slow query detected - execution time 15s",
            "Cache: Redis connection timeout",
            "API: Endpoint /api/users returning 500 errors",
            "Monitoring: Alert threshold exceeded for disk usage",
            "Backup: Incremental backup completed in 5 minutes",
            "Security: Unauthorized access attempt blocked",
            "Performance: Database connection pool at 90% capacity"
        ]

        # Create log entries over the past 14 days with more realistic distribution
        for i in range(300):  # Create 300 sample logs
            # Create more logs in recent days, fewer in older days
            days_ago = random.choices(
                range(14), 
                weights=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            )[0]
            
            timestamp = timezone.now() - timedelta(
                days=days_ago,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            
            # Weight log types - more info logs, fewer errors
            log_type = random.choices(
                log_types,
                weights=[0.15, 0.25, 0.45, 0.15]  # error, warning, info, debug
            )[0]
            
            log_entry = LogEntry.objects.create(
                timestamp=timestamp,
                host_ip=random.choice(hosts),
                log_message=random.choice(log_messages),
                source=random.choice(sources),
                log_type=log_type
            )
            
            # Create anomalies for some log entries (about 25%)
            if random.random() < 0.25:
                # Higher anomaly scores for errors and warnings
                if log_type in ['error', 'warning']:
                    anomaly_score = random.uniform(0.7, 0.98)
                else:
                    anomaly_score = random.uniform(0.6, 0.9)
                    
                Anomaly.objects.create(
                    log_entry=log_entry,
                    anomaly_score=anomaly_score,
                    threshold=0.5,
                    is_anomaly=anomaly_score > 0.5
                )

        self.stdout.write(f'Created {LogEntry.objects.count()} log entries')

    def create_sample_anomalies(self):
        """Create additional sample anomalies"""
        # Get some log entries that don't have anomalies yet
        logs_without_anomalies = LogEntry.objects.filter(anomalies__isnull=True)[:20]
        
        for log_entry in logs_without_anomalies:
            anomaly_score = random.uniform(0.7, 0.98)
            Anomaly.objects.create(
                log_entry=log_entry,
                anomaly_score=anomaly_score,
                threshold=0.5,
                is_anomaly=True
            )

        self.stdout.write(f'Created {Anomaly.objects.count()} anomalies')

    def create_system_status(self):
        """Create system status entries"""
        services = [
            {'name': 'kafka', 'status': 'running', 'details': 'Kafka broker is running on port 9092'},
            {'name': 'zookeeper', 'status': 'running', 'details': 'Zookeeper service is healthy'},
            {'name': 'consumer', 'status': 'running', 'details': 'Log consumer process is active'},
            {'name': 'database', 'status': 'running', 'details': 'PostgreSQL database is online'},
            {'name': 'redis', 'status': 'running', 'details': 'Redis cache server is responding'},
        ]
        
        for service in services:
            SystemStatus.objects.create(
                service_name=service['name'],
                status=service['status'],
                details=service['details']
            )

        self.stdout.write(f'Created {SystemStatus.objects.count()} system status entries')

    def create_platform_settings(self):
        """Create platform settings"""
        PlatformSettings.objects.create(
            anomaly_threshold=0.5,
            kafka_broker_url='localhost:9092',
            kafka_topic_logs='logs',
            kafka_topic_anomalies='anomalies'
        )

        self.stdout.write('Created platform settings')

    def create_streamlit_optimized_data(self):
        """Create additional data optimized for Streamlit visualizations"""
        self.stdout.write('Creating Streamlit-optimized data...')
        
        # Create time-series data for charts
        # Add more recent data with hourly distribution for better charts
        current_time = timezone.now()
        
        for hour in range(24):  # Last 24 hours
            for minute in range(0, 60, 15):  # Every 15 minutes
                timestamp = current_time - timedelta(hours=hour, minutes=minute)
                
                # Create logs with realistic patterns
                if hour in [9, 10, 11, 14, 15, 16]:  # Peak hours
                    num_logs = random.randint(3, 8)
                else:  # Off-peak hours
                    num_logs = random.randint(1, 3)
                
                for _ in range(num_logs):
                    log_entry = LogEntry.objects.create(
                        timestamp=timestamp + timedelta(seconds=random.randint(0, 900)),
                        host_ip=random.choice(['192.168.1.100', '192.168.1.101', '10.0.0.50']),
                        log_message=random.choice([
                            "API request processed successfully",
                            "Database query completed",
                            "User authentication successful",
                            "Cache hit - data served from memory",
                            "Load balancer health check passed",
                            "Monitoring metrics collected",
                            "Backup verification completed",
                            "Security scan finished - no threats found"
                        ]),
                        source=random.choice(['web_server', 'database', 'api_gateway']),
                        log_type=random.choices(['info', 'debug'], weights=[0.8, 0.2])[0]
                    )
                    
                    # Create some anomalies during peak hours
                    if hour in [10, 15] and random.random() < 0.3:
                        Anomaly.objects.create(
                            log_entry=log_entry,
                            anomaly_score=random.uniform(0.75, 0.95),
                            threshold=0.5,
                            is_anomaly=True
                        )

        self.stdout.write('Created Streamlit-optimized time-series data') 