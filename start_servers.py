#!/usr/bin/env python3
"""
Start both API server and static file server
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path
from port_config import API_PORT, STATIC_PORT, API_HOST, print_port_info

def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_file = Path('.env')
    if env_file.exists():
        print("📄 Loading environment variables from .env file...")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Environment variables loaded from .env file")
    else:
        print("ℹ️  No .env file found, using system environment variables")

def signal_handler(sig, frame):
    print('\n👋 Shutting down servers...')
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 Starting Movie Database Servers")
    print("=" * 50)
    
    # Load environment variables from .env file first
    load_env_file()
    
    # Start API server
    print(f"📡 Starting API server on port {API_PORT}...")
    api_process = subprocess.Popen([
        sys.executable, '-m', 'uvicorn', 
        'api:app', 
        '--reload', 
        '--host', API_HOST, 
        '--port', str(API_PORT)
    ])
    
    # Wait a moment for API server to start
    time.sleep(3)
    
    # Start static file server
    print(f"🌐 Starting static file server on port {STATIC_PORT}...")
    static_process = subprocess.Popen([
        sys.executable, 'serve_static.py'
    ])
    
    print("\n✅ Both servers are running!")
    print_port_info()
    
    print("\n🔧 Developer Tools:")
    print("   - Use the developer tools in the main app to login to admin")
    print(f"   - API base should be set to: http://127.0.0.1:{API_PORT}")
    print("   - Default admin credentials: admin / admin123")
    
    print("\nPress Ctrl+C to stop both servers")
    
    try:
        # Wait for both processes
        api_process.wait()
        static_process.wait()
    except KeyboardInterrupt:
        print("\n👋 Stopping servers...")
        api_process.terminate()
        static_process.terminate()
        api_process.wait()
        static_process.wait()
        print("✅ Servers stopped")

if __name__ == "__main__":
    main()
