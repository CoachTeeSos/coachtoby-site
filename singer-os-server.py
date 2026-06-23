#!/usr/bin/env python3
"""Singer OS Server — Sheet writer + Leaderboard API"""
import json, time, subprocess, os, sys, urllib.request, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN_PATH = os.path.join(os.path.expanduser('~'), '.hermes', 'google_token.json')
SHEET_ID = '1P9zZYOwKDaARmyGsfEyEhcwMoMX-tW0yTPAHNiMHB18'
PORT = 3000

def get_access_token():
    with open(TOKEN_PATH) as f:
        token_data = json.load(f)
    try:
        expiry = float(token_data.get('expiry', '0'))
        if time.time() > expiry - 300:
            print('Refreshing token...', file=sys.stderr)
            result = subprocess.run([
                'curl', '-s', '-X', 'POST',
                token_data['token_uri'],
                '-d', f'client_id={token_data["client_id"]}&client_secret={token_data["client_secret"]}&refresh_token={token_data["refresh_token"]}&grant_type=refresh_token'
            ], capture_output=True, text=True, timeout=15)
            new_token = json.loads(result.stdout)
            token_data['access_token'] = new_token['access_token']
            token_data['expiry'] = time.time() + new_token.get('expires_in', 3600)
            with open(TOKEN_PATH, 'w') as f:
                json.dump(token_data, f)
            print('Token refreshed', file=sys.stderr)
        return token_data['access_token']
    except Exception as e:
        print(f'Token error: {e}', file=sys.stderr)
        return token_data.get('access_token', '')

def sheet_append(range_name, values):
    """Append a row to the Google Sheet"""
    token = get_access_token()
    if not token:
        return {'error': 'no_token'}
    
    url = f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{range_name}:append?valueInputOption=USER_ENTERED'
    data = json.dumps({'values': [values]}).encode()
    
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except Exception as e:
        print(f'Sheet append error: {e}', file=sys.stderr)
        return {'error': str(e)}

def sheet_read(range_name):
    """Read from the Google Sheet"""
    token = get_access_token()
    if not token:
        return None
    
    url = f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{range_name}'
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        return data.get('values', [])
    except Exception as e:
        print(f'Sheet read error: {e}', file=sys.stderr)
        return None

def compute_leaderboard():
    """Read all scores and compute daily/weekly/monthly top 10"""
    # Read from Scores tab (create if doesn't exist)
    rows = sheet_read('Scores!A:E')
    
    if not rows or len(rows) <= 1:
        # No data yet — return empty leaderboards
        return {
            'daily': [], 'weekly': [], 'monthly': [],
            'message': 'No scores yet. Be the first to complete an exercise!'
        }
    
    # Parse: Timestamp | Name | Email | XP | Exercise
    headers = rows[0]
    data = rows[1:]
    
    now = time.time()
    day_start = now - 86400
    week_start = now - 7 * 86400
    month_start = now - 30 * 86400
    
    # Aggregate by user
    def aggregate(start_time):
        scores = {}
        for row in data:
            if len(row) < 4:
                continue
            try:
                ts = float(row[0])
                if ts < start_time:
                    continue
                name = row[1] or 'Anonymous'
                email = row[2] or ''
                xp = int(row[3]) if row[3].isdigit() else 0
                key = email or name
                if key not in scores:
                    scores[key] = {'name': name, 'email': email, 'xp': 0, 'sessions': 0}
                scores[key]['xp'] += xp
                scores[key]['sessions'] += 1
            except (ValueError, IndexError):
                continue
        # Sort by XP descending
        ranked = sorted(scores.values(), key=lambda x: x['xp'], reverse=True)
        return ranked[:10]
    
    return {
        'daily': aggregate(day_start),
        'weekly': aggregate(week_start),
        'monthly': aggregate(month_start)
    }

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        
        path = self.path
        
        if path == '/submit':
            # Registration submission
            name = data.get('name', '')
            email = data.get('email', '')
            whatsapp = data.get('whatsapp', '')
            ip = data.get('ip', '')
            token = data.get('token', '')
            
            result = sheet_append('Registrations!A:F', [
                time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                name, email, whatsapp, ip, token
            ])
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}).encode())
        
        elif path == '/score':
            # Score submission (from exercises)
            name = data.get('name', 'Anonymous')
            email = data.get('email', '')
            xp = data.get('xp', 0)
            exercise = data.get('exercise', 'unknown')
            
            result = sheet_append('Scores!A:E', [
                str(int(time.time())),
                name,
                email,
                str(xp),
                exercise
            ])
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        path = self.path
        
        if path == '/leaderboard':
            lb = compute_leaderboard()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(lb).encode())
        
        elif path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True, 'time': time.time()}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logs

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f'Singer OS server running on port {PORT}', file=sys.stderr)
    server.serve_forever()
