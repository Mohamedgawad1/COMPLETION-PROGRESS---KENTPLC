#!/usr/bin/env python3
"""
PS5 Completion Platform - Local Server
Serves index.html and provides /api/rebuild to rebuild from XLSX files.
Run: python serve.py
Open: http://localhost:8080
"""
import http.server
import json
import os
import subprocess
import sys
import threading
from urllib.parse import urlparse

PORT = 8080
DIR = os.path.dirname(os.path.abspath(__file__))
REBUILD_SCRIPT = os.path.join(DIR, 'rebuild_data.py')

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/rebuild':
            self._handle_rebuild()
        elif parsed.path == '/api/update-all':
            self._handle_update_all()
        else:
            self.send_error(404)

    def _handle_rebuild(self):
        try:
            if not os.path.exists(REBUILD_SCRIPT):
                self._json_response(500, {'ok': False, 'error': f'Rebuild script not found: {REBUILD_SCRIPT}'})
                return

            result = subprocess.run(
                [sys.executable, REBUILD_SCRIPT],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0:
                self._json_response(200, {'ok': True, 'output': result.stdout[-500:]})
            else:
                self._json_response(500, {'ok': False, 'error': result.stderr[-500:], 'output': result.stdout[-500:]})
        except subprocess.TimeoutExpired:
            self._json_response(500, {'ok': False, 'error': 'Rebuild timed out (120s)'})
        except Exception as e:
            self._json_response(500, {'ok': False, 'error': str(e)})

    def _handle_update_all(self):
        steps = []
        try:
            # Step 1: Rebuild from XLSX
            steps.append('Rebuilding from XLSX...')
            if not os.path.exists(REBUILD_SCRIPT):
                self._json_response(500, {'ok': False, 'error': 'Rebuild script not found', 'steps': steps})
                return
            r = subprocess.run([sys.executable, REBUILD_SCRIPT], capture_output=True, text=True, timeout=120, cwd=DIR)
            if r.returncode != 0:
                self._json_response(500, {'ok': False, 'error': f'Rebuild failed: {r.stderr[-300:]}', 'steps': steps})
                return
            steps.append('Rebuild OK')

            # Step 2: git add
            steps.append('Git add...')
            r = subprocess.run(['git', 'add', 'index.html'], capture_output=True, text=True, timeout=30, cwd=DIR)
            if r.returncode != 0:
                self._json_response(500, {'ok': False, 'error': f'git add failed: {r.stderr}', 'steps': steps})
                return
            steps.append('Git add OK')

            # Step 3: git commit
            steps.append('Git commit...')
            r = subprocess.run(['git', 'commit', '-m', 'Update all from XLSX (auto)', '--no-verify'], capture_output=True, text=True, timeout=30, cwd=DIR)
            if r.returncode != 0 and 'nothing to commit' not in r.stdout:
                self._json_response(500, {'ok': False, 'error': f'git commit failed: {r.stderr}', 'steps': steps})
                return
            steps.append('Git commit OK')

            # Step 4: git push
            steps.append('Git push...')
            r = subprocess.run(['git', 'push', 'origin', 'main', '--no-verify'], capture_output=True, text=True, timeout=60, cwd=DIR)
            if r.returncode != 0:
                self._json_response(500, {'ok': False, 'error': f'git push failed: {r.stderr}', 'steps': steps})
                return
            steps.append('Git push OK — site updated!')

            self._json_response(200, {'ok': True, 'steps': steps, 'output': r.stdout[-300:]})
        except subprocess.TimeoutExpired:
            self._json_response(500, {'ok': False, 'error': 'Timed out', 'steps': steps})
        except Exception as e:
            self._json_response(500, {'ok': False, 'error': str(e), 'steps': steps})

    def _json_response(self, code, data):
        body = json.dumps(data).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        if '/api/rebuild' in str(args):
            print(f"[REBUILD] {args[0]}")
        elif not str(args[0]).startswith('GET /') or 'index.html' in str(args[0]):
            super().log_message(format, *args)

if __name__ == '__main__':
    print(f"PS5 Dashboard Server: http://localhost:{PORT}")
    print(f"Rebuild script: {REBUILD_SCRIPT}")
    print(f"Press Ctrl+C to stop\n")
    server = http.server.HTTPServer(('127.0.0.1', PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
