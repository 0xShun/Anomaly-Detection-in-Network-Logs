#!/usr/bin/env python
import os
import django
import re

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webplatform.settings')
django.setup()

from dashboard.models import LogEntry

def classify_log_level(log_message):
    """
    Classify log level based on keywords in the log message
    """
    message_lower = log_message.lower()
    
    # Error level indicators
    error_keywords = ['error', 'exception', 'fail', 'critical', 'fatal', 'crash', 'abort']
    # Warning level indicators  
    warning_keywords = ['warn', 'warning', 'deprecated', 'caution', 'alert']
    # Info level indicators
    info_keywords = ['info', 'information', 'notice', 'debug', 'trace']
    
    for keyword in error_keywords:
        if keyword in message_lower:
            return 'error'
            
    for keyword in warning_keywords:
        if keyword in message_lower:
            return 'warning'
            
    for keyword in info_keywords:
        if keyword in message_lower:
            return 'info'
    
    return 'unknown'

def analyze_current_logs():
    """
    Analyze current logs to see how log types are determined
    """
    print("Analyzing current log type classification...")
    logs = LogEntry.objects.all()[:20]  # Get first 20 logs
    
    print(f"Total logs: {LogEntry.objects.count()}")
    print("\nSample log entries and their types:")
    print("-" * 80)
    
    for log in logs:
        predicted_type = classify_log_level(log.log_message)
        current_type = log.log_type or 'none'
        
        print(f"Message: {log.log_message[:60]}...")
        print(f"Current type: {current_type}")
        print(f"Predicted type: {predicted_type}")
        print(f"Match: {'✓' if current_type == predicted_type else '✗'}")
        print("-" * 40)

if __name__ == "__main__":
    analyze_current_logs()
