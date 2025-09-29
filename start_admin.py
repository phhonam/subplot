#!/usr/bin/env python3
"""
Startup script for the Movie Database Admin Interface
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path
from port_config import API_PORT, print_port_info

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

def check_environment():
    """Check if required environment variables are set"""
    # TMDB_API_KEY is only required for scraping functionality
    optional_vars = ['TMDB_API_KEY', 'OMDB_API_KEY']
    missing_optional = []
    
    for var in optional_vars:
        if not os.environ.get(var):
            missing_optional.append(var)
    
    if missing_optional:
        print("⚠️  Optional environment variables not set:")
        for var in missing_optional:
            print(f"   - {var}")
        print("\nThese are only needed for movie scraping functionality.")
        print("Basic admin operations (hide/show movies) will work without them.")
    
    print("✅ Environment variables check passed")
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'requests',
        'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required Python packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nPlease install them with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ Dependencies check passed")
    return True

def check_files():
    """Check if required files exist"""
    required_files = [
        'api.py',
        'admin_api.py',
        'admin_auth.py',
        'admin.html',
        'admin_login.html',
        'admin.js',
        'movie_profiles_merged.json'
    ]
    
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ Required files check passed")
    return True

def setup_default_credentials():
    """Set up default admin credentials if not configured"""
    if not os.environ.get('ADMIN_USERNAME'):
        os.environ['ADMIN_USERNAME'] = 'admin'
        print("ℹ️  Using default admin username: admin")
    
    if not os.environ.get('ADMIN_PASSWORD_HASH'):
        import hashlib
        default_password = 'admin123'
        os.environ['ADMIN_PASSWORD_HASH'] = hashlib.sha256(default_password.encode()).hexdigest()
        print("ℹ️  Using default admin password: admin123")
        print("⚠️  Please change these credentials in production!")
    
    if not os.environ.get('ADMIN_JWT_SECRET'):
        import secrets
        os.environ['ADMIN_JWT_SECRET'] = secrets.token_urlsafe(32)
        print("ℹ️  Generated random JWT secret")

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting Movie Database Admin Interface...")
    print_port_info()
    print("\nPress Ctrl+C to stop the server")
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'api:app', 
            '--reload', 
            '--host', '0.0.0.0', 
            '--port', str(API_PORT)
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

def main():
    """Main startup function"""
    print("🎬 Movie Database Admin Interface Startup")
    print("=" * 50)
    
    # Load environment variables from .env file first
    load_env_file()
    
    # Run checks
    if not check_environment():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    if not check_files():
        sys.exit(1)
    
    # Setup default credentials
    setup_default_credentials()
    
    print("\n✅ All checks passed! Starting server...")
    
    # Optionally open browser (non-blocking)
    try:
        import threading
        import time
        
        def open_browser():
            time.sleep(2)  # Wait for server to start
            webbrowser.open(f'http://127.0.0.1:{API_PORT}/admin_login.html')
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        print("🌐 Browser will open automatically in 2 seconds...")
    except Exception:
        print(f"🌐 You can manually open: http://127.0.0.1:{API_PORT}/admin_login.html")
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()
