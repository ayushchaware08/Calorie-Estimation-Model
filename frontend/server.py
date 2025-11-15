"""
Simple HTTP server for the frontend
Run this to serve the frontend on http://localhost:8080
"""

import http.server
import socketserver
import os
import sys

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Enable CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def run_server():
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║      🍽️  Food Calorie Estimation Frontend Server         ║
║                                                           ║
║  Server running at: http://localhost:{PORT}               ║
║                                                           ║
║  Make sure the backend is running on port 8000           ║
║  Make sure the dashboard is running on port 8501         ║
║                                                           ║
║  Press Ctrl+C to stop the server                         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✓ Server stopped")
            sys.exit(0)

if __name__ == "__main__":
    run_server()
