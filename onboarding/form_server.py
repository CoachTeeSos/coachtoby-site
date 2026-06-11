#!/usr/bin/env python3
"""
Simple HTTP server for receiving form submissions from the website.
Writes to local SQLite DB. Runs on port 5000.
"""
import os, sys, json, logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

sys.path.insert(0, "/home/user/workspace")
from local_db import init_db, add_registration, load_env

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
load_env()

init_db()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/register':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_json(400, {'error': 'Invalid JSON'})
                return

            # Map form fields to DB fields
            service_key = data.get('Service Key', data.get('service_key', ''))
            svc_label = data.get('Plan', data.get('plan', ''))

            # Determine sessions
            if service_key in ('monthly', 'ngn-monthly'):
                total_sessions = 4
            elif service_key in ('single', 'ngn-single'):
                total_sessions = 1
            else:
                total_sessions = 0

            # Determine status
            is_free = service_key in ('free-community', 'free-call', 'quiz', 'lead-magnet', 'abuja-collective')
            status = 'Active' if is_free else 'Awaiting Receipt'

            try:
                rid = add_registration({
                    'name': data.get('Name', data.get('name', '')),
                    'email': data.get('Email', data.get('email', '')),
                    'phone': data.get('Phone', data.get('phone', '')),
                    'telegram': data.get('Telegram', data.get('telegram', '')),
                    'location': data.get('Location', data.get('location', '')),
                    'plan': svc_label,
                    'service_key': service_key,
                    'status': status,
                    'source': 'Website',
                    'total_sessions': total_sessions,
                    'sessions_used': 0,
                    'budget': data.get('Budget', data.get('budget', '')),
                    'needs': data.get('Needs', data.get('needs', '')),
                })
                logger.info("Registration received: " + data.get('Name', '') + " (ID: " + str(rid) + ")")
                self.send_json(201, {'success': True, 'id': rid})
            except Exception as e:
                logger.error("Registration failed: " + str(e))
                self.send_json(500, {'error': str(e)})
        else:
            self.send_json(404, {'error': 'Not found'})

    def do_GET(self):
        if self.path == '/api/health':
            from local_db import get_stats
            self.send_json(200, {'status': 'ok', 'stats': get_stats()})
        else:
            self.send_json(404, {'error': 'Not found'})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # Suppress default logging


if __name__ == '__main__':
    port = int(os.environ.get('FORM_PORT', 5000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    logger.info("Form server running on port " + str(port))
    server.serve_forever()
