"""
Nostromo Terminal — CRT display renderer.
Scanlines, vignette, phosphor glow, character rendering.
"""

import pygame
from . import config as cfg


class CRTRenderer:
    """Handles all CRT visual effects and text rendering."""

    def __init__(self, screen, font):
        self.font = font

        metrics = font.size("M")
        self.char_w = metrics[0]
        self.char_h = metrics[1]

        # Scanline overlay
        self.scanline_surface = pygame.Surface(
            (cfg.SCREEN_W, cfg.SCREEN_H), pygame.SRCALPHA
        )
        for y in range(0, cfg.SCREEN_H, 2):
            pygame.draw.line(
                self.scanline_surface, cfg.COLOR_SCANLINE,
                (0, y), (cfg.SCREEN_W, y)
            )

        # Phosphor glow surface
        self.glow_surface = pygame.Surface(
            (cfg.SCREEN_W, cfg.SCREEN_H), pygame.SRCALPHA
        )

        # Vignette
        self.vignette = self._make_vignette()

    def _make_vignette(self):
        surf = pygame.Surface((cfg.SCREEN_W, cfg.SCREEN_H), pygame.SRCALPHA)
        cx, cy = cfg.SCREEN_W // 2, cfg.SCREEN_H // 2
        max_dist = (cx**2 + cy**2) ** 0.5
        for radius in range(int(max_dist), int(max_dist * 0.6), -2):
            alpha = int(50 * (radius / max_dist) ** 3)
            alpha = min(alpha, 50)
            pygame.draw.circle(surf, (0, 0, 0, alpha), (cx, cy), radius)
        return surf

    def render_char(self, char, col, row, color=None, glow=False):
        """Render a single character at grid position."""
        if color is None:
            color = cfg.COLOR_TEXT
        screen = pygame.display.get_surface()
        x = col * self.char_w + 4
        y = row * self.char_h + 4

        if glow:
            glow_surf = self.font.render(char, True, cfg.COLOR_GLOW[:3])
            glow_surf.set_alpha(cfg.COLOR_GLOW[3])
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.glow_surface.blit(glow_surf, (x + dx, y + dy))

        char_surf = self.font.render(char, True, color)
        screen.blit(char_surf, (x, y))

    def render_text_line(self, text, row, color=None):
        """Render a full line of text at given row."""
        if color is None:
            color = cfg.COLOR_TEXT
        for i, ch in enumerate(text):
            if i >= cfg.COLS:
                break
            self.render_char(ch, i, row, color)

    def draw_cursor(self, col, row, visible):
        """Draw block cursor at position."""
        if not visible:
            return
        screen = pygame.display.get_surface()
        x = col * self.char_w + 4
        y = row * self.char_h + 4
        cursor_rect = pygame.Rect(x, y, self.char_w, self.char_h)
        pygame.draw.rect(screen, cfg.COLOR_CURSOR, cursor_rect)

    def draw_separator(self, row):
        """Draw a horizontal separator line above given row."""
        screen = pygame.display.get_surface()
        sep_y = row * self.char_h - 2
        pygame.draw.line(
            screen, cfg.COLOR_DIM,
            (4, sep_y), (cfg.SCREEN_W - 4, sep_y)
        )

    def apply_effects(self):
        """Apply CRT post-processing: glow, scanlines, vignette."""
        screen = pygame.display.get_surface()
        screen.blit(self.glow_surface, (0, 0))
        self.glow_surface.fill((0, 0, 0, 0))
        screen.blit(self.scanline_surface, (0, 0))
        screen.blit(self.vignette, (0, 0))
