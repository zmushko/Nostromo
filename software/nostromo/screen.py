"""
Nostromo Terminal — screen interface.
Base class for all switchable applications in the terminal.
"""

import pygame


class Screen:
    """Base class for switchable terminal screens.

    Every application (Claude, Mother, YTPlay, Menu) extends this.
    ScreenManager calls these methods to orchestrate switching.

    Subclasses MUST implement:
        handle_event(event) — process pygame event
        update()            — per-frame logic (called for ALL alive screens)
        render(surface)     — draw to screen (called only for active screen)

    Subclasses MAY override:
        on_activate()       — called when screen gains focus
        on_deactivate()     — called when screen loses focus
        is_alive()          — return True if update() needed when inactive
        wants_global_key()  — return False to block Ctrl+N switching
    """

    def __init__(self, name, shortcut_label=None):
        """
        Args:
            name: display name (e.g. "CLAUDE", "MU-TH-UR")
            shortcut_label: key hint (e.g. "C-1", "C-2")
        """
        self.name = name
        self.shortcut_label = shortcut_label or ""
        self.active = False
        self.initialized = False

    def init(self, renderer):
        """Lazy initialization — called on first activation.

        Override to set up heavy resources (API clients, etc).
        Always call super().init(renderer).
        """
        self.renderer = renderer
        self.initialized = True

    def handle_event(self, event):
        """Process a pygame event. Return True if consumed."""
        return False

    def update(self):
        """Per-frame logic. Called for ALL screens where is_alive() is True."""
        pass

    def render(self):
        """Draw to the display. Called ONLY for the active screen."""
        pass

    def on_activate(self):
        """Called when this screen becomes active (gains focus)."""
        self.active = True

    def on_deactivate(self):
        """Called when this screen loses focus."""
        self.active = False

    def is_alive(self):
        """Return True if this screen needs update() when inactive.

        Override for background tasks (e.g. audio playback).
        Default: False — inactive screens are fully paused.
        """
        return False

    def cleanup(self):
        """Release resources on shutdown."""
        pass

    @property
    def show_status_bar(self):
        """Return False to hide status bar (e.g. during fullscreen video)."""
        return True
