#!/usr/bin/env python3
"""
Quick test runner - starts server and runs tests
"""
import subprocess
import time
import sys
import signal

def main():
    print("🚀 Starting Django server...")
    
    # Start Django server
    server_process = subprocess.Popen(
        ['python3', 'manage.py', 'runserver'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    try:
        # Run tests
        print("🧪 Running tests...\n")
        result = subprocess.run(['python3', 'test_local_api.py'])
        exit_code = result.returncode
        
    finally:
        # Stop server
        print("\n🛑 Stopping server...")
        server_process.send_signal(signal.SIGINT)
        server_process.wait(timeout=5)
        print("✅ Server stopped")
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
