"""Public read-only HTTPS overlay via a Cloudflare Quick Tunnel.

No remote user can invoke counter actions: only overlay HTML, the background
image, and filtered public statistics are routed through the tunnel.
"""
import json
import os
import re
import subprocess
import sys
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

PORT = 8766
TUNNEL_PATTERN = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com(?:/)?", re.I)

class PublicLinkService:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.lock = threading.RLock()
        self.server = None
        self.process = None
        self.url = ""
        self.status = "Not connected"
        self.error = ""
        self.stopping = False

    def get_state(self):
        with self.lock:
            return {"url": self.url, "status": self.status, "error": self.error}

    def _proxy_handler(self):
        snapshot = self.snapshot

        class PublicHandler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                self.send_error(405, "Read-only overlay")

            def do_GET(self):
                path = urlsplit(self.path).path
                if path not in ("/", "/overlay", "/api/state", "/api/events", "/pirate-theme.png"):
                    return self.send_error(404, "Not found")
                if path == "/api/events":
                    # Event-driven live updates avoid background browser timer throttling.
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                    self.send_header("Cache-Control", "no-cache, no-transform")
                    self.send_header("X-Accel-Buffering", "no")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    last_payload = None
                    last_heartbeat = 0.0
                    try:
                        while True:
                            s = snapshot()
                            public = {
                                "chests": int(s.get("chests", 0)),
                                "tokens": int(s.get("tokens", 0)),
                                "username": str(s.get("username", "default")),
                            }
                            payload = json.dumps(public, separators=(",", ":"))
                            now = time.monotonic()
                            if payload != last_payload:
                                self.wfile.write(("data: " + payload + "\\n\\n").encode("utf-8"))
                                self.wfile.flush()
                                last_payload = payload
                                last_heartbeat = now
                            elif now - last_heartbeat >= 12:
                                self.wfile.write(b": ping\\n\\n")
                                self.wfile.flush()
                                last_heartbeat = now
                            time.sleep(0.12)
                    except (BrokenPipeError, ConnectionResetError, OSError):
                        pass
                    return
                try:
                    if path == "/api/state":
                        s = snapshot()
                        public = {
                            "chests": int(s.get("chests", 0)),
                            "tokens": int(s.get("tokens", 0)),
                            "username": str(s.get("username", "default")),
                        }
                        body = json.dumps(public).encode("utf-8")
                        content_type = "application/json"
                    else:
                        local_path = "/overlay" if path == "/" else path
                        with urlopen("http://127.0.0.1:8765" + local_path, timeout=5) as response:
                            body = response.read(5_000_000)
                            content_type = "image/png" if path == "/pirate-theme.png" else "text/html; charset=utf-8"
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.send_header("Referrer-Policy", "no-referrer")
                    self.end_headers()
                    self.wfile.write(body)
                except Exception:
                    self.send_error(503, "Tracker unavailable")
        return PublicHandler

    def start(self):
        with self.lock:
            if self.status in ("Connecting...", "Connected"):
                return
            self.stopping = False
            self.url = ""
            self.error = ""
            self.status = "Connecting..."
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            with self.lock:
                if self.server is None:
                    self.server = ThreadingHTTPServer(("127.0.0.1", PORT), self._proxy_handler())
                    threading.Thread(target=self.server.serve_forever, daemon=True).start()
            base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
            tool = base / "cloudflared.exe"
            if not tool.is_file():
                raise FileNotFoundError("Cloudflare tunnel component is missing. Reinstall the latest Treasure Tracker.")
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            command = [str(tool), "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{PORT}"]
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                       stdin=subprocess.DEVNULL, text=True, errors="replace",
                                       bufsize=1, creationflags=flags)
            with self.lock:
                self.process = process
            for line in process.stderr:
                with self.lock:
                    if self.stopping:
                        break
                match = TUNNEL_PATTERN.search(line)
                if match:
                    with self.lock:
                        self.url = match.group(0).rstrip("/") + "/overlay"
                        self.status = "Connected"
                        self.error = ""
            returncode = process.wait()
            with self.lock:
                if not self.stopping:
                    self.url = ""
                    self.status = "Disconnected"
                    self.error = f"Cloudflare connection closed (code {returncode}). Check your internet connection."
        except Exception as exc:
            with self.lock:
                self.url = ""
                self.status = "Connection failed"
                self.error = str(exc)

    def stop(self):
        with self.lock:
            self.stopping = True
            process = self.process
            self.process = None
            self.url = ""
            self.status = "Not connected"
            self.error = ""
        if process and process.poll() is None:
            process.terminate()
