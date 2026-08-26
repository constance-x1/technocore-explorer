#!/usr/bin/env python3
"""
Launcher for Technocore DID Explorer
Starts the local server and optionally opens the dashboard in your default web browser.
"""

from __future__ import annotations

import os
import sys
import webbrowser
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(errors="backslashreplace")
        except Exception:
            pass

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import run_standalone

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8080))
    url = f"http://{host}:{port}"
    
    print(f"Starting Technocore DID Explorer on {url}...", flush=True)
    
    try:
        webbrowser.open(url)
    except Exception:
        pass

    run_standalone(host, port)
