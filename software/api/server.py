"""
NOSTROMO Remote API — HTTP server for receiving commands from mobile app.
Runs in a background thread alongside the main pygame loop.

Usage:
    from api.server import RemoteAPI
    api = RemoteAPI(port=8080, play_callback=my_func)
    api.start()
"""

import re
import sys
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler


def extract_video_id(text):
    """Extract YouTube video ID from URL or raw 11-char ID."""
    patterns = [
        r'(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', text.strip()):
        return text.strip()
    return None


class _Handler(BaseHTTPRequestHandler):
    """HTTP request handler for Nostromo Remote API."""

    def do_POST(self):
        routes = {
            "/play": self._handle_play,
            "/seek": self._handle_seek,
            "/volume": self._handle_volume,
            "/pause": self._handle_pause,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self._respond(404, {"error": "not found"})

    def do_GET(self):
        if self.path == "/ping":
            self._respond(200, {"status": "ok", "name": "NOSTROMO"})
        elif self.path == "/status":
            self._handle_status()
        else:
            self._respond(404, {"error": "not found"})

    def _handle_play(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
        except Exception:
            self._respond(400, {"error": "bad request"})
            return

        url = data.get("url", "")
        video_id = extract_video_id(url)
        if not video_id:
            self._respond(400, {"error": "no video ID found", "url": url})
            return

        # Queue play command for MediaTerminal (thread-safe)
        api = self.server.api
        if api and api.play_callback:
            api.play_callback(video_id, url)
            print(f"[api] queued play: {video_id}", file=sys.stderr)
            self._respond(200, {"status": "queued", "video_id": video_id})
        else:
            self._respond(503, {"error": "media terminal not ready"})

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            return json.loads(body)
        except Exception:
            return None

    def _get_player(self):
        api = self.server.api
        return api.get_player() if api and api.get_player else None

    def _handle_seek(self):
        data = self._read_json()
        if not data or "seconds" not in data:
            self._respond(400, {"error": "need 'seconds' field"})
            return
        player = self._get_player()
        if not player or not player.playing:
            self._respond(503, {"error": "nothing playing"})
            return
        player.seek(float(data["seconds"]))
        self._respond(200, {"status": "ok"})

    def _handle_volume(self):
        data = self._read_json()
        if not data or "delta" not in data:
            self._respond(400, {"error": "need 'delta' field"})
            return
        player = self._get_player()
        if not player:
            self._respond(503, {"error": "player not ready"})
            return
        player.set_volume(float(data["delta"]))
        self._respond(200, {"status": "ok", "volume": int(player.volume * 100)})

    def _handle_pause(self):
        player = self._get_player()
        if not player or not player.playing:
            self._respond(503, {"error": "nothing playing"})
            return
        player.toggle_pause()
        self._respond(200, {"status": "ok", "paused": player.paused})

    def _handle_status(self):
        player = self._get_player()
        if not player:
            self._respond(200, {"playing": False})
            return
        self._respond(200, {
            "playing": player.playing,
            "paused": player.paused if player.playing else False,
            "position": round(player.position, 1) if player.playing else 0,
            "duration": round(player.duration, 1) if player.playing else 0,
            "volume": int(player.volume * 100),
            "muted": player.muted,
        })

    def _respond(self, code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        """Redirect HTTP logs to stderr."""
        print(f"[api] {args[0]}", file=sys.stderr)


class RemoteAPI:
    """HTTP API server running in a background thread."""

    def __init__(self, port=8080, play_callback=None, get_player=None):
        self.port = port
        self.play_callback = play_callback
        self.get_player = get_player
        self._server = None
        self._thread = None

    def start(self):
        """Start the API server in a daemon thread."""
        self._server = HTTPServer(("0.0.0.0", self.port), _Handler)
        self._server.api = self  # pass reference to handler
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True
        )
        self._thread.start()
        print(f"[api] listening on port {self.port}", file=sys.stderr)

    def stop(self):
        """Shutdown the server."""
        if self._server:
            self._server.shutdown()
            print("[api] stopped", file=sys.stderr)
            