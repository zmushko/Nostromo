#!/usr/bin/env python3
"""
NOSTROMO SYSTEMS
=================
Multi-screen terminal for Raspberry Pi 5.

Screens:
    Ctrl+1  — CLAUDE (AI assistant)
    Ctrl+2  — MU-TH-UR 6000 (ship mainframe)
    Ctrl+3  — MEDIA (YouTube player)
    Ctrl+4  — CONFIG (system settings)
    Ctrl+Q  — shutdown

Remote API:
    POST http://<host>:8080/play    {"url": "https://youtube.com/watch?v=..."}
    POST http://<host>:8080/seek    {"seconds": 10}  (negative to rewind)
    POST http://<host>:8080/volume  {"delta": 0.1}   (negative to lower)
    POST http://<host>:8080/pause
    GET  http://<host>:8080/ping
    GET  http://<host>:8080/status

Usage:
    export ANTHROPIC_API_KEY="your-key"
    python3 main.py [--fullscreen]
"""

import os
import sys
import faulthandler
faulthandler.enable()

# Verify API key early
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
    sys.exit(1)

from nostromo import app
from nostromo.manager import ScreenManager

from screens import claude, mother, ytplay, settings
from api.server import RemoteAPI


def main():
    screen, renderer, clock = app.init_display("NOSTROMO SYSTEMS")

    mgr = ScreenManager(renderer, clock)

    # Register screens — first one becomes active
    mgr.add("1", claude.create())
    mgr.add("2", mother.create())
    mgr.add("3", ytplay.create())
    mgr.add("4", settings.create())

    # Force-init media screen so Remote API works from any screen
    media_screen = mgr.screens["3"]
    if not media_screen.initialized:
        media_screen.init(renderer)

    def _on_remote_play(vid, url):
        media_screen.terminal.queue_play(vid, url)
        mgr.set_active("3")

    api = RemoteAPI(
        port=8080,
        play_callback=_on_remote_play,
        get_player=lambda: media_screen.terminal.video_player,
    )
    api.start()

    # Start with Claude
    mgr.set_active("1")

    print("[nostromo] ready — Ctrl+1/2/3/4 switch, Ctrl+Q quit",
          file=sys.stderr)

    mgr.run()


if __name__ == "__main__":
    main()
    