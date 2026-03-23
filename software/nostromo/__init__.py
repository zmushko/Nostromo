"""
Nostromo Terminal Framework
============================
CRT-style terminal toolkit for Raspberry Pi.

Modules:
    config   — colors, timing, geometry
    crt      — CRT renderer (scanlines, vignette, glow)
    terminal — base terminal (boot, input, scrollback)
    keyboard — EN/RU layout switching
    logger   — session logging
    sound    — synthesized terminal sounds
    screen   — base Screen interface
    manager  — ScreenManager (multi-screen orchestration)
    app      — pygame init and display setup
"""

from .terminal import BaseTerminal
from .logger import SessionLogger
from .crt import CRTRenderer
from .keyboard import KeyboardLayout
from .screen import Screen
from . import config
from . import sound
from . import app
