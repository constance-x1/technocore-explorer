"""
Technocore DID Explorer - Web Server & API Gateway
Provides concurrent REST API endpoints for querying DID intelligence and serves the Frontend Dashboard.
Uses ThreadingHTTPServer for multithreaded non-blocking request handling.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Safe stream reconfigure for Windows console Unicode handling
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(errors="backslashreplace")
        except Exception:
            pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.scanner import (
    DEFAULT_BASE_URL,
    ensure_background_collector_started,
    scan_did_agent,
    scan_network_overview,
    validate_did,
)

FRONTEND_DIR = BASE_DIR / "frontend"


# ---------------------------------------------------------------------------
# Multi-threaded Built-in HTTP Server (Zero External Dependencies)
# ---------------------------------------------------------------------------
class ExplorerRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

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

        # Health Check
        if path == "/api/health":
            self._send_json(200, {
                "status": "healthy",
                "app": "Technocore DID Explorer",
                "network_target": DEFAULT_BASE_URL,
            })
            return

        # Network Overview & Active DIDs
        if path in ("/api/overview", "/api/rooms"):
            data = scan_network_overview()
            self._send_json(200, data)
            return

        # DID Scan: /api/scan?did=... OR /api/scan/<did>
        if path == "/api/scan" or path.startswith("/api/scan/"):
            target_did = ""
            if path.startswith("/api/scan/"):
                target_did = urllib.parse.unquote(path[len("/api/scan/") :])
            elif "did" in query and query["did"]:
                target_did = query["did"][0].strip()

            if not target_did:
                self._send_json(400, {"error": "Missing 'did' parameter"})
                return

            data = scan_did_agent(target_did)
            self._send_json(200, data)
            return

        # Fallback to serving frontend files
        if path in ("", "/"):
            self.path = "/index.html"
        super().do_GET()

    def _send_json(self, status: int, payload: dict):
        response_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)


def run_standalone(host: str = "127.0.0.1", port: int = 8080):
    # Start background collector daemon
    ensure_background_collector_started(DEFAULT_BASE_URL)

    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, ExplorerRequestHandler)
    print(f"\n=======================================================")
    print(f" [*] Technocore DID Explorer & OSINT Web Tool Live!")
    print(f" [*] Access Dashboard: http://{host}:{port}")
    print(f" [*] Target Network:   {DEFAULT_BASE_URL}")
    print(f"=======================================================\n", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...", flush=True)
        httpd.server_close()


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8080))
    run_standalone(host, port)
