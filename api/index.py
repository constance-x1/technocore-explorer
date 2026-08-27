"""
Vercel Serverless Function: /api/index
Router and fallback handler for all API requests.
"""

from __future__ import annotations

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler

try:
    from .scanner import (
        DEFAULT_BASE_URL,
        scan_did_agent,
        scan_network_overview,
        validate_did,
    )
except ImportError:
    from scanner import (
        DEFAULT_BASE_URL,
        scan_did_agent,
        scan_network_overview,
        validate_did,
    )


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
            path = parsed.path.rstrip("/")
            query = urllib.parse.parse_qs(parsed.query)

            # 1. Health check
            if path.endswith("/health") or "health" in query:
                self._send_json(200, {
                    "status": "healthy",
                    "app": "Technocore DID Explorer (Serverless API)",
                    "network_target": DEFAULT_BASE_URL,
                })
                return

            # 2. Network overview
            if path.endswith("/overview") or path.endswith("/rooms") or "overview" in query:
                data = scan_network_overview()
                self._send_json(200, data)
                return

            # 3. DID Scan (either /api/scan or ?did=...)
            if "/scan" in path or "did" in query:
                target_did = ""
                if "did" in query and query["did"]:
                    target_did = query["did"][0].strip()
                elif "/scan/" in path:
                    target_did = urllib.parse.unquote(path.split("/scan/", 1)[1].strip())

                if not target_did:
                    self._send_json(400, {"status": "error", "error": "Missing 'did' parameter"})
                    return

                data = scan_did_agent(target_did)
                self._send_json(200, data)
                return

            # 4. Default overview for root API call
            data = scan_network_overview()
            self._send_json(200, data)
        except Exception as e:
            self._send_json(500, {"status": "error", "error": f"API error: {str(e)}"})

    def _send_json(self, status: int, payload: dict):
        response_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)
