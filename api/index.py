"""
Vercel Serverless Function Entry Point for Technocore DID Explorer
Handles API routing on Vercel's serverless infrastructure.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.scanner import (
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
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path.rstrip("/")
        query = urllib.parse.parse_qs(parsed.query)

        # Health check
        if path.endswith("/health"):
            self._send_json(200, {
                "status": "healthy",
                "app": "Technocore DID Explorer (Vercel Serverless)",
                "network_target": DEFAULT_BASE_URL,
            })
            return

        # Network overview
        if path.endswith("/overview") or path.endswith("/rooms"):
            data = scan_network_overview()
            self._send_json(200, data)
            return

        # DID Scan: /api/scan?did=... OR /api/scan/<did>
        if "/scan" in path:
            target_did = ""
            if path.startswith("/api/scan/") or "/scan/" in path:
                parts = path.split("/scan/", 1)
                if len(parts) > 1 and parts[1]:
                    target_did = urllib.parse.unquote(parts[1])
            elif "did" in query and query["did"]:
                target_did = query["did"][0].strip()

            if not target_did:
                self._send_json(400, {"error": "Missing 'did' parameter"})
                return

            data = scan_did_agent(target_did)
            self._send_json(200, data)
            return

        # Default fallback
        self._send_json(200, {
            "status": "online",
            "service": "Technocore Explorer API",
            "endpoints": ["/api/health", "/api/overview", "/api/scan?did=<did>"]
        })

    def _send_json(self, status: int, payload: dict):
        response_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)
