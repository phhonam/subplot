#!/usr/bin/env python3
"""
Simple HTTP server to serve static files (HTML, CSS, JS)
"""

import http.server
import socketserver
import os
import urllib.request
import socket
from pathlib import Path
from port_config import STATIC_PORT, API_URL

PORT = STATIC_PORT
DIRECTORY = Path(__file__).parent

# Set default socket timeout to prevent hanging
socket.setdefaulttimeout(10)

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def do_GET(self):
        # Proxy /api/* requests to the API server
        if self.path.startswith('/api/'):
            try:
                # Forward request to API server
                api_url = f"{API_URL}{self.path[4:]}"  # Remove /api prefix
                req = urllib.request.Request(api_url)
                
                # Forward headers
                for header, value in self.headers.items():
                    req.add_header(header, value)
                
                # Make request to API with timeout (10 seconds)
                with urllib.request.urlopen(req, timeout=10) as response:
                    # Send response
                    self.send_response(response.status)
                    for header, value in response.headers.items():
                        if header.lower() not in ['content-encoding', 'transfer-encoding', 'connection']:
                            self.send_header(header, value)
                    self.end_headers()
                    self.wfile.write(response.read())
                return
            except socket.timeout:
                print(f"Timeout proxying to API: {self.path}")
                self.send_response(504)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": "API server timeout"}')
                return
            except Exception as e:
                print(f"Error proxying to API: {e}")
                self.send_response(502)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": "API server error"}')
                return
        
        # Otherwise serve static files
        return super().do_GET()
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
        # Add cache-busting headers for JSON files to prevent caching issues
        # Fix: Check if self.path exists before using it
        if hasattr(self, 'path') and self.path and self.path.endswith('.json'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        
        super().end_headers()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Multi-threaded TCP server to handle concurrent requests"""
    allow_reuse_address = True
    daemon_threads = True

def main():
    os.chdir(DIRECTORY)
    
    with ThreadedTCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
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
