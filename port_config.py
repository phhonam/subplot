#!/usr/bin/env python3
"""
Centralized port configuration for Movie Recommender application
"""

# API Server Configuration
API_PORT = 8003
API_HOST = "0.0.0.0"
API_URL = f"http://127.0.0.1:{API_PORT}"

# Static File Server Configuration  
STATIC_PORT = 8004
STATIC_HOST = "127.0.0.1"
STATIC_URL = f"http://{STATIC_HOST}:{STATIC_PORT}"

# All ports used by the application (for clearing)
ALL_PORTS = [8000, 8001, 8002, 8003, 8004]

# URL endpoints
ENDPOINTS = {
    "main_app": f"{STATIC_URL}/index.html",
    "admin_login": f"{STATIC_URL}/admin_login.html", 
    "admin_panel": f"{STATIC_URL}/admin.html",
    "api_server": API_URL,
    "api_docs": f"{API_URL}/docs",
    "health_check": f"{API_URL}/health"
}

def get_port_config():
    """Get the complete port configuration"""
    return {
        "api": {
            "port": API_PORT,
            "host": API_HOST,
            "url": API_URL
        },
        "static": {
            "port": STATIC_PORT,
            "host": STATIC_HOST,
            "url": STATIC_URL
        },
        "endpoints": ENDPOINTS,
        "all_ports": ALL_PORTS
    }

def print_port_info():
    """Print formatted port information"""
    print("🚀 Movie Recommender Port Configuration")
    print("=" * 50)
    print(f"📡 API Server: {API_URL}")
    print(f"🌐 Static Server: {STATIC_URL}")
    print(f"\n📊 Access Points:")
    print(f"   🎬 Main App: {ENDPOINTS['main_app']}")
    print(f"   🔐 Admin Login: {ENDPOINTS['admin_login']}")
    print(f"   📊 Admin Panel: {ENDPOINTS['admin_panel']}")
    print(f"   📡 API Server: {ENDPOINTS['api_server']}")
    print(f"   📚 API Docs: {ENDPOINTS['api_docs']}")

if __name__ == "__main__":
    print_port_info()
