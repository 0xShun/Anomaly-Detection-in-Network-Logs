from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from dashboard.models import LogEntry, Anomaly


class Command(BaseCommand):
    help = 'Performance analysis and optimization utilities'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze current performance metrics',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear all caches',
        )
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='Optimize SQLite database (VACUUM)',
        )
        parser.add_argument(
            '--slow-queries',
            action='store_true',
            help='Show slow query analysis',
        )

    def handle(self, *args, **options):
        if options['analyze']:
            self.analyze_performance()
        
        if options['clear_cache']:
            self.clear_all_caches()
        
        if options['vacuum']:
            self.vacuum_database()
        
        if options['slow_queries']:
            self.analyze_slow_queries()

    def analyze_performance(self):
        """Analyze current performance metrics"""
        self.stdout.write(self.style.SUCCESS('=== Performance Analysis ==='))
        
        # Database stats
        total_logs = LogEntry.objects.count()
        total_anomalies = Anomaly.objects.count()
        
        self.stdout.write(f"📊 Database Records:")
        self.stdout.write(f"   • Log Entries: {total_logs:,}")
        self.stdout.write(f"   • Anomalies: {total_anomalies:,}")
        
        # Recent activity
        last_24h = timezone.now() - timedelta(hours=24)
        recent_logs = LogEntry.objects.filter(timestamp__gte=last_24h).count()
        recent_anomalies = Anomaly.objects.filter(detected_at__gte=last_24h).count()
        
        self.stdout.write(f"\n📈 Last 24 Hours:")
        self.stdout.write(f"   • New Logs: {recent_logs:,}")
        self.stdout.write(f"   • New Anomalies: {recent_anomalies:,}")
        self.stdout.write(f"   • Logs/Hour: {recent_logs/24:.1f}")
        
        # Cache stats
        try:
            cache_stats = cache.get('cache_stats', {})
            if cache_stats:
                self.stdout.write(f"\n💾 Cache Performance:")
                for key, value in cache_stats.items():
                    self.stdout.write(f"   • {key}: {value}")
        except:
            self.stdout.write(f"\n💾 Cache: In-memory cache (no stats available)")
        
        # Database size (SQLite specific)
        try:
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA page_count;")
                page_count = cursor.fetchone()[0]
                cursor.execute("PRAGMA page_size;")
                page_size = cursor.fetchone()[0]
                db_size = (page_count * page_size) / (1024 * 1024)  # MB
                
                self.stdout.write(f"\n💽 Database Size:")
                self.stdout.write(f"   • Size: {db_size:.1f} MB")
                self.stdout.write(f"   • Pages: {page_count:,}")
        except Exception as e:
            self.stdout.write(f"\n💽 Database Size: Error getting size ({e})")

    def clear_all_caches(self):
        """Clear all application caches"""
        self.stdout.write(self.style.WARNING('🧹 Clearing all caches...'))
        
        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS('✅ All caches cleared successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error clearing caches: {e}'))

    def vacuum_database(self):
        """Optimize SQLite database"""
        self.stdout.write(self.style.WARNING('🔧 Optimizing SQLite database...'))
        
        try:
            with connection.cursor() as cursor:
                # Get database size before
                cursor.execute("PRAGMA page_count;")
                pages_before = cursor.fetchone()[0]
                
                # Run VACUUM
                cursor.execute("VACUUM;")
                
                # Get database size after
                cursor.execute("PRAGMA page_count;")
                pages_after = cursor.fetchone()[0]
                
                pages_saved = pages_before - pages_after
                percentage_saved = (pages_saved / pages_before) * 100 if pages_before > 0 else 0
                
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Database optimized: {pages_saved:,} pages saved ({percentage_saved:.1f}%)'
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error optimizing database: {e}'))

    def analyze_slow_queries(self):
        """Analyze potentially slow queries"""
        self.stdout.write(self.style.SUCCESS('=== Slow Query Analysis ==='))
        
        # Common expensive queries
        queries_to_test = [
            ("Count all logs", "SELECT COUNT(*) FROM dashboard_logentry"),
            ("Count by log type", "SELECT log_type, COUNT(*) FROM dashboard_logentry GROUP BY log_type"),
            ("Recent logs", "SELECT * FROM dashboard_logentry ORDER BY timestamp DESC LIMIT 100"),
            ("Anomalies with logs", """
                SELECT a.*, l.log_message 
                FROM dashboard_anomaly a 
                JOIN dashboard_logentry l ON a.log_entry_id = l.id 
                ORDER BY a.detected_at DESC LIMIT 50
            """),
        ]
        
        for query_name, query in queries_to_test:
            try:
                import time
                start_time = time.time()
                
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    results = cursor.fetchall()
                
                duration = time.time() - start_time
                
                if duration > 1.0:
                    status = self.style.ERROR(f'❌ SLOW ({duration:.3f}s)')
                elif duration > 0.5:
                    status = self.style.WARNING(f'⚠️  ({duration:.3f}s)')
                else:
                    status = self.style.SUCCESS(f'✅ ({duration:.3f}s)')
                
                self.stdout.write(f"{query_name}: {status}")
                
            except Exception as e:
                self.stdout.write(f"{query_name}: {self.style.ERROR(f'❌ Error: {e}')}")

        # Index usage analysis (SQLite specific)
        try:
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA index_list('dashboard_logentry');")
                indexes = cursor.fetchall()
                
                self.stdout.write(f"\n📋 Indexes on LogEntry table:")
                for index in indexes:
                    self.stdout.write(f"   • {index[1]} ({'UNIQUE' if index[2] else 'NON-UNIQUE'})")
                
        except Exception as e:
            self.stdout.write(f"\n📋 Index analysis error: {e}")
