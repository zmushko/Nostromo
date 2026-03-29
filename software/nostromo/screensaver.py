"""
Nostromo Terminal — screensaver.
Activates after idle timeout. Modes: logo, matrix, status, dvd.
"""

import math
import random
import time
import pygame
from . import config as cfg


# Weyland-Yutani ASCII logo
_LOGO = [
    "     ██╗    ██╗ ██╗   ██╗",
    "     ██║    ██║ ╚██╗ ██╔╝",
    "     ██║ █╗ ██║  ╚████╔╝ ",
    "     ██║███╗██║   ╚██╔╝  ",
    "     ╚███╔███╔╝    ██║   ",
    "      ╚══╝╚══╝     ╚═╝   ",
    "",
    "    W E Y L A N D - Y U T A N I",
    "      BUILDING BETTER WORLDS",
]


class Screensaver:
    """Manages idle detection and screensaver rendering."""

    def __init__(self, renderer):
        self.renderer = renderer
        self.active = False
        self._last_input = time.time()
        self._start_time = 0
        # Full screen rows (including input area and status bar)
        self._total_rows = cfg.STATUS_ROW + 1

        # Matrix rain state
        self._columns = []
        self._matrix_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<>{}[]|/\\!@#$%"

        # DVD bounce state
        self._dvd_x = 0.0
        self._dvd_y = 0.0
        self._dvd_dx = 60.0
        self._dvd_dy = 40.0

        # Status scroll state
        self._scroll_offset = 0.0

        self._last_tick = 0

    def reset_timer(self):
        """Call on any user input to reset idle timer."""
        self._last_input = time.time()
        if self.active:
            self.active = False

    def update(self):
        """Check idle timeout, return True if screensaver is active."""
        if cfg.SCREENSAVER_MODE == "off":
            self.active = False
            return False

        if not self.active:
            elapsed = time.time() - self._last_input
            if elapsed >= cfg.SCREENSAVER_TIMEOUT:
                self._activate()
        return self.active

    def _activate(self):
        self.active = True
        self._start_time = time.time()
        self._last_tick = time.time()

        # Init matrix columns
        self._columns = []
        for c in range(cfg.COLS):
            self._columns.append({
                "pos": random.randint(-self._total_rows, 0),
                "speed": random.uniform(0.15, 0.5),
                "chars": [random.choice(self._matrix_chars) for _ in range(self._total_rows)],
            })

        # Init DVD position
        self._dvd_x = float(cfg.SCREEN_W // 4)
        self._dvd_y = float(cfg.SCREEN_H // 3)

        # Init scroll
        self._scroll_offset = 0.0

    def render(self, surface):
        """Render the active screensaver."""
        now = time.time()
        dt = now - self._last_tick
        self._last_tick = now

        surface.fill(cfg.COLOR_BG)

        mode = cfg.SCREENSAVER_MODE
        if mode == "logo":
            self._render_logo(now)
        elif mode == "matrix":
            self._render_matrix(dt)
        elif mode == "status":
            self._render_status(dt)
        elif mode == "dvd":
            self._render_dvd(dt)

    def _render_logo(self, now):
        """Pulsing Weyland-Yutani ASCII logo."""
        r = self.renderer
        elapsed = now - self._start_time
        pulse = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(elapsed * 1.5))

        color = (
            int(cfg.COLOR_TEXT[0] * pulse),
            int(cfg.COLOR_TEXT[1] * pulse),
            int(cfg.COLOR_TEXT[2] * pulse),
        )

        start_row = (self._total_rows - len(_LOGO)) // 2
        for i, line in enumerate(_LOGO):
            col_offset = (cfg.COLS - len(line)) // 2
            for j, ch in enumerate(line):
                if ch != " " and col_offset + j < cfg.COLS:
                    r.render_char(ch, col_offset + j, start_row + i, color)

    def _render_matrix(self, dt):
        """Falling green characters."""
        r = self.renderer
        for c, col in enumerate(self._columns):
            col["pos"] += col["speed"]
            head = int(col["pos"])

            for row in range(self._total_rows):
                dist = head - row
                if dist < 0 or dist > self._total_rows:
                    continue

                if dist == 0:
                    col["chars"][row % len(col["chars"])] = random.choice(self._matrix_chars)

                brightness = max(0.0, 1.0 - dist / self._total_rows)
                color = (
                    int(cfg.COLOR_TEXT[0] * brightness * 0.3),
                    int(cfg.COLOR_TEXT[1] * brightness),
                    int(cfg.COLOR_TEXT[2] * brightness * 0.3),
                )

                if dist == 0:
                    color = cfg.COLOR_BRIGHT

                ch = col["chars"][row % len(col["chars"])]
                r.render_char(ch, c, row, color)

            if head > self._total_rows + random.randint(5, 15):
                col["pos"] = random.randint(-10, -1)
                col["speed"] = random.uniform(0.15, 0.5)

    def _render_status(self, dt):
        """Scrolling status messages."""
        r = self.renderer
        messages = [
            "NOSTROMO SYSTEMS NOMINAL",
            "CREW STATUS: HYPERSLEEP",
            "COURSE: THEDUS — LV-426",
            "ETA: 10 MONTHS",
            "CARGO: 20,000,000 TONS MINERAL ORE",
            "REFINERY STATUS: OPERATIONAL",
            "HULL INTEGRITY: 100%",
            "LIFE SUPPORT: ACTIVE",
            "MU-TH-UR 6000: ONLINE",
            "SPECIAL ORDER 937: CLASSIFIED",
        ]

        self._scroll_offset += dt * 2.0

        total_height = len(messages) * 3
        offset = self._scroll_offset % (total_height + self._total_rows)

        for i, msg in enumerate(messages):
            row = int(i * 3 - offset + self._total_rows)
            if 0 <= row < self._total_rows:
                col_offset = (cfg.COLS - len(msg)) // 2
                for j, ch in enumerate(msg):
                    if 0 <= col_offset + j < cfg.COLS:
                        r.render_char(ch, col_offset + j, row, cfg.COLOR_TEXT)

            sep_row = int(i * 3 + 1 - offset + self._total_rows)
            if 0 <= sep_row < self._total_rows:
                dots = "· " * (len(msg) // 2)
                col_offset = (cfg.COLS - len(dots)) // 2
                for j, ch in enumerate(dots):
                    if 0 <= col_offset + j < cfg.COLS:
                        r.render_char(ch, col_offset + j, sep_row, cfg.COLOR_DIM)

    def _render_dvd(self, dt):
        """Bouncing MU-TH-UR 6000 text."""
        r = self.renderer
        text = "MU-TH-UR 6000"
        text_w = len(text) * r.char_w
        text_h = r.char_h

        self._dvd_x += self._dvd_dx * dt
        self._dvd_y += self._dvd_dy * dt

        max_x = cfg.SCREEN_W - text_w - 8
        max_y = cfg.SCREEN_H - text_h - 8

        if self._dvd_x <= 4 or self._dvd_x >= max_x:
            self._dvd_dx = -self._dvd_dx
            self._dvd_x = max(4.0, min(self._dvd_x, float(max_x)))
        if self._dvd_y <= 4 or self._dvd_y >= max_y:
            self._dvd_dy = -self._dvd_dy
            self._dvd_y = max(4.0, min(self._dvd_y, float(max_y)))

        # Render at pixel position using font directly
        screen = pygame.display.get_surface()
        surf = r.font.render(text, True, cfg.COLOR_TEXT)
        screen.blit(surf, (int(self._dvd_x), int(self._dvd_y)))

