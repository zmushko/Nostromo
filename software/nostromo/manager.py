"""
Nostromo Terminal — screen manager.
Manages multiple screens, handles switching, runs main loop.
"""

import sys
import pygame
from . import config as cfg
from . import sound


class ScreenManager:
    """Manages multiple Screen instances with hot-switching.

    Ctrl+1..9  — switch to screen by slot number
    F10        — toggle menu screen (if registered)
    Ctrl+Q     — quit

    Screens are registered with add(). First added screen
    becomes the initial active screen unless set_active() is called.
    """

    def __init__(self, renderer, clock):
        self.renderer = renderer
        self.clock = clock
        self.screens = {}        # slot -> Screen
        self.active_key = None   # current active slot key
        self.menu_key = None     # slot key for menu screen
        self._running = False
        self._on_quit = None

    @property
    def active(self):
        """Currently active screen."""
        if self.active_key and self.active_key in self.screens:
            return self.screens[self.active_key]
        return None

    def add(self, key, screen):
        """Register a screen at a slot key (e.g. "1", "2", "menu").

        Args:
            key: slot identifier
            screen: Screen instance
        """
        self.screens[key] = screen
        if self.active_key is None:
            self.active_key = key

    def set_menu(self, key):
        """Designate a screen as the menu (toggled via F10)."""
        self.menu_key = key

    def set_active(self, key):
        """Switch to a screen by slot key."""
        if key not in self.screens:
            return
        if key == self.active_key:
            return

        old = self.active
        if old:
            old.on_deactivate()

        self.active_key = key
        new_screen = self.screens[key]

        # Lazy init on first activation
        if not new_screen.initialized:
            new_screen.init(self.renderer)

        new_screen.on_activate()

    def run(self, on_quit=None):
        """Main loop — run until quit."""
        self._on_quit = on_quit
        self._running = True

        # Initialize the first active screen
        active = self.active
        if active and not active.initialized:
            active.init(self.renderer)
            active.on_activate()

        try:
            while self._running:
                try:
                    self._process_events()
                    self._update_all()
                    self._render()
                    self.clock.tick(cfg.FPS)
                except (SystemError, pygame.error):
                    continue
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    def quit(self):
        """Request quit from within a screen."""
        self._running = False

    def _process_events(self):
        """Process pygame events — global keys first, then active screen."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
                return

            if event.type == pygame.KEYDOWN:
                # Global: Ctrl+Q = quit
                if event.key == pygame.K_q and (event.mod & pygame.KMOD_CTRL):
                    self._running = False
                    return

                # Global: Ctrl+1..9 = switch screen
                if event.mod & pygame.KMOD_CTRL:
                    num = self._key_to_number(event.key)
                    if num is not None:
                        key = str(num)
                        if key in self.screens:
                            self.set_active(key)
                            continue

                # Global: F10 = toggle menu
                if event.key == pygame.K_F10 and self.menu_key:
                    if self.active_key == self.menu_key:
                        # Return to previous screen
                        if hasattr(self, '_prev_key') and self._prev_key:
                            self.set_active(self._prev_key)
                    else:
                        self._prev_key = self.active_key
                        self.set_active(self.menu_key)
                    continue

                # Pass to active screen
                active = self.active
                if active:
                    active.handle_event(event)
            else:
                # Non-keyboard events to active screen
                active = self.active
                if active:
                    active.handle_event(event)

    def _update_all(self):
        """Update all alive screens."""
        for key, screen in self.screens.items():
            if not screen.initialized:
                continue
            if screen.active or screen.is_alive():
                screen.update()

    def _render(self):
        """Render active screen + status bar."""
        surface = pygame.display.get_surface()
        if surface is None:
            return

        surface.fill(cfg.COLOR_BG)

        active = self.active
        if active:
            active.render()

        # Status bar (skip during fullscreen video etc.)
        if active and active.show_status_bar:
            self._render_status_bar()

        self.renderer.apply_effects()
        pygame.display.flip()

    def _render_status_bar(self):
        """Render bottom status bar with screen tabs."""
        r = self.renderer
        bar_row = cfg.STATUS_ROW

        parts = []
        for key, screen in self.screens.items():
            if key == self.menu_key:
                continue  # don't show menu in tab bar
            if not screen.initialized:
                label = f" {key}:{screen.name} "
            else:
                label = f" {key}:{screen.name} "

            parts.append((key, label))

        col = 0
        for key, label in parts:
            is_active = (key == self.active_key)
            color = cfg.COLOR_TEXT if is_active else cfg.COLOR_DIM
            for ch in label:
                if col < cfg.COLS:
                    r.render_char(ch, col, bar_row, color)
                    col += 1

    def _key_to_number(self, key):
        """Convert pygame key to number 1-9, or None."""
        mapping = {
            pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3,
            pygame.K_4: 4, pygame.K_5: 5, pygame.K_6: 6,
            pygame.K_7: 7, pygame.K_8: 8, pygame.K_9: 9,
        }
        return mapping.get(key)

    def _cleanup(self):
        """Shutdown all screens."""
        for screen in self.screens.values():
            if screen.initialized:
                screen.cleanup()
        if self._on_quit:
            self._on_quit()
