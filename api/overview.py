"""
Vercel Serverless Function: /api/overview
Returns active rooms, sequence cursors, and recently active DIDs.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

try:
    from .scanner import scan_network_overview
except ImportError:
    from scanner import scan_network_overview


class handler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        try:
            result = scan_network_overview()
            self._send_json(200, result)
        except Exception as e:
            self._send_json(500, {"status": "error", "error": f"Overview failed: {str(e)}"})

    def _send_json(self, status: int, payload: dict):
        response_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)
