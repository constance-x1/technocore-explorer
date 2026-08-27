"""
Vercel Serverless Function: /api/scan
Scans a single DID and returns its lifecycle, messages, and social attribution.
"""

from __future__ import annotations

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler

try:
    from .scanner import scan_did_agent, validate_did
except ImportError:
    from scanner import scan_did_agent, validate_did


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
            parsed = urllib.parse.urlsplit(self.path)
            query = urllib.parse.parse_qs(parsed.query)

            target_did = ""
            if "did" in query and query["did"]:
                target_did = query["did"][0].strip()
            elif "/scan/" in parsed.path:
                target_did = urllib.parse.unquote(parsed.path.split("/scan/", 1)[1].strip())

            if not target_did:
                self._send_json(400, {"status": "error", "error": "Missing 'did' parameter"})
                return

            result = scan_did_agent(target_did)
            self._send_json(200, result)
        except Exception as e:
            self._send_json(500, {"status": "error", "error": f"Scan failed: {str(e)}"})

    def _send_json(self, status: int, payload: dict):
        response_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)
