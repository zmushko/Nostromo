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

# Claude crab — body parts as pixel grids (from SVG)
# Each pixel = "██" (2 chars). Coordinates in pixel units.
# Body: torso 11x7 at (2,0), arms 2x2, eyes 1x2, legs 1x2
_CRAB_BODY = [
    # (x, y, w, h) in pixel units
    (2, 0, 11, 7),   # torso
]
_CRAB_LEFT_EYE = (4, 2)    # 1x2
_CRAB_RIGHT_EYE = (10, 2)  # 1x2
_CRAB_LEFT_ARM = (0, 3, 2, 2)
_CRAB_RIGHT_ARM = (13, 3, 2, 2)
_CRAB_LEGS = [
    (3, 7, "a"),   # outer left
    (5, 7, "b"),   # inner left
    (9, 7, "a"),   # inner right
    (11, 7, "b"),  # outer right
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
        elif mode == "crab":
            self._render_crab(now)

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

    def _render_crab(self, now):
        """Animated Claude crab — component animation from SVG source."""
        r = self.renderer
        elapsed = now - self._start_time
        t = elapsed  # shorthand

        # Animation phase (1s cycle, 4 keyframes like SVG)
        phase = (t % 1.0)

        # Body bob (SVG: 0,1 → 0,0 → 0,1 → 0,0)
        if phase < 0.25:
            body_dy = 1
        elif phase < 0.5:
            body_dy = 0
        elif phase < 0.75:
            body_dy = 1
        else:
            body_dy = 0

        # Leg-a offsets (SVG: -2,0 → 0,0 → 2,0 → 0,-2)
        if phase < 0.25:
            leg_a_dx, leg_a_dy = -1, 0
        elif phase < 0.5:
            leg_a_dx, leg_a_dy = 0, 0
        elif phase < 0.75:
            leg_a_dx, leg_a_dy = 1, 0
        else:
            leg_a_dx, leg_a_dy = 0, -1

        # Leg-b offsets (SVG: 2,0 → 0,-2 → -2,0 → 0,0)
        if phase < 0.25:
            leg_b_dx, leg_b_dy = 1, 0
        elif phase < 0.5:
            leg_b_dx, leg_b_dy = 0, -1
        elif phase < 0.75:
            leg_b_dx, leg_b_dy = -1, 0
        else:
            leg_b_dx, leg_b_dy = 0, 0

        # Arm offsets (SVG: 0,0 → 0,-1/+1 → 0,0 → 0,+1/-1)
        if phase < 0.25:
            arm_l_dy, arm_r_dy = 0, 0
        elif phase < 0.5:
            arm_l_dy, arm_r_dy = -1, 1
        elif phase < 0.75:
            arm_l_dy, arm_r_dy = 0, 0
        else:
            arm_l_dy, arm_r_dy = 1, -1

        # Eye blink (SVG: scaleY=0.1 at 50% of 4s cycle)
        blink_phase = (t % 4.0) / 4.0
        is_blinking = 0.49 < blink_phase < 0.52

        # Scale factor: each SVG pixel = 2 chars wide, 1 row tall
        # Crab is ~15 pixels wide (30 chars), ~9 pixels tall (9 rows)
        crab_w = 15
        crab_h = 9
        base_col = (cfg.COLS - crab_w * 2) // 2
        base_row = (self._total_rows - crab_h) // 2

        color = cfg.COLOR_TEXT

        def put(px, py, c=None):
            """Draw a pixel (2 chars wide) at pixel coords."""
            col = base_col + px * 2
            row = base_row + py
            if 0 <= row < self._total_rows and 0 <= col + 1 < cfg.COLS:
                r.render_char("█", col, row, c or color)
                r.render_char("█", col + 1, row, c or color)

        # Torso (x=2..12, y=0..6) + body bob
        for px in range(2, 13):
            for py in range(0, 7):
                put(px, py + body_dy)

        # Left arm (x=0..1, y=3..4) + body bob + arm offset
        for px in range(0, 2):
            for py in range(3, 5):
                put(px, py + body_dy + arm_l_dy)

        # Right arm (x=13..14, y=3..4) + body bob + arm offset
        for px in range(13, 15):
            for py in range(3, 5):
                put(px, py + body_dy + arm_r_dy)

        # Eyes (punch holes — draw in background color) + body bob
        if not is_blinking:
            eye_color = cfg.COLOR_BG
            for py in range(2, 4):
                put(4, py + body_dy, eye_color)
                put(10, py + body_dy, eye_color)
        else:
            # Blink — draw thin line instead of full eyes
            put(4, 3 + body_dy, cfg.COLOR_BG)
            put(10, 3 + body_dy, cfg.COLOR_BG)

        # Legs
        for lx, ly, group in _CRAB_LEGS:
            if group == "a":
                dx, dy = leg_a_dx, leg_a_dy
            else:
                dx, dy = leg_b_dx, leg_b_dy
            for py in range(ly, ly + 2):
                put(lx + dx, py + dy)

        # Shadow
        shadow_color = cfg.COLOR_DIM
        for px in range(3, 12):
            put(px, 9, shadow_color)

        # Label
        text = "C L A U D E"
        text_col = (cfg.COLS - len(text)) // 2
        text_row = base_row + 12
        if text_row < self._total_rows:
            for j, ch in enumerate(text):
                c = text_col + j
                if ch != " " and 0 <= c < cfg.COLS:
                    r.render_char(ch, c, text_row, cfg.COLOR_DIM)

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

