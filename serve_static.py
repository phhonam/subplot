#!/usr/bin/env python3
"""
Simple HTTP server to serve static files (HTML, CSS, JS)
"""

import http.server
import socketserver
import os
from pathlib import Path
from port_config import STATIC_PORT

PORT = STATIC_PORT
DIRECTORY = Path(__file__).parent

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
        # Add cache-busting headers for JSON files to prevent caching issues
        if self.path.endswith('.json'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        
        super().end_headers()

def main():
    os.chdir(DIRECTORY)
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"🌐 Static file server running at http://127.0.0.1:{PORT}")
        print(f"📁 Serving files from: {DIRECTORY}")
        print(f"🔐 Admin Login: http://127.0.0.1:{PORT}/admin_login.html")
        print(f"📊 Admin Panel: http://127.0.0.1:{PORT}/admin.html")
        print(f"🎬 Main App: http://127.0.0.1:{PORT}/index.html")
        print("\nPress Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
