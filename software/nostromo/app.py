"""
Nostromo Terminal — application runner.
Handles pygame init, font loading, geometry calculation, main loop.
"""

import os
import sys
import pygame
from . import config as cfg
from .crt import CRTRenderer
from . import sound


def find_mono_font():
    """Find a suitable monospace font on the system."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def init_display(title="NOSTROMO TERMINAL", input_rows=None):
    """Initialize pygame and calculate terminal geometry.

    Returns (screen, renderer, clock).
    Also updates cfg.COLS, cfg.ROWS, cfg.INPUT_ROWS.
    """
    pygame.init()

    flags = 0
    if "--fullscreen" in sys.argv or os.environ.get("NOSTROMO_FULLSCREEN"):
        flags = pygame.FULLSCREEN

    screen = pygame.display.set_mode((cfg.SCREEN_W, cfg.SCREEN_H), flags)
    pygame.display.set_caption(title)
    clock = pygame.time.Clock()

    if flags & pygame.FULLSCREEN:
        pygame.mouse.set_visible(False)

    # Load font
    font_path = find_mono_font()
    if font_path:
        font = pygame.font.Font(font_path, cfg.FONT_SIZE)
    else:
        font = pygame.font.SysFont("monospace", cfg.FONT_SIZE)

    pygame.key.set_repeat(400, 50)

    # Calculate terminal geometry
    if input_rows is not None:
        cfg.INPUT_ROWS = input_rows

    actual_char_w, actual_char_h = font.size("M")
    margin = 8
    cfg.COLS = (cfg.SCREEN_W - margin) // actual_char_w
    available_h = cfg.SCREEN_H - margin
    total_rows = available_h // actual_char_h
    cfg.ROWS = total_rows - cfg.INPUT_ROWS - 2  # -1 separator, -1 status bar
    cfg.STATUS_ROW = total_rows - 1

    print(f"[nostromo] Font: {actual_char_w}x{actual_char_h}px, "
          f"terminal: {cfg.COLS}x{cfg.ROWS}+{cfg.INPUT_ROWS}")

    renderer = CRTRenderer(screen, font)
    sound.init()
    return screen, renderer, clock


def run(screen, renderer, clock, terminal, on_quit=None):
    """Standard main loop.

    Args:
        screen: pygame display surface
        renderer: CRTRenderer
        clock: pygame.time.Clock
        terminal: object with update(), render(), handle_key(event) methods
        on_quit: optional cleanup callback
    """
    running = True
    try:
        while running:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q and (event.mod & pygame.KMOD_CTRL):
                            running = False
                        else:
                            terminal.handle_key(event)

                terminal.update()

                current_screen = pygame.display.get_surface()
                if current_screen is None:
                    continue
                current_screen.fill(cfg.COLOR_BG)
                terminal.render()
                renderer.apply_effects()
                pygame.display.flip()

                clock.tick(cfg.FPS)
            except (SystemError, pygame.error):
                # Display was re-initialized, skip this frame
                continue
    except KeyboardInterrupt:
        pass
    finally:
        if on_quit:
            on_quit()

    pygame.quit()
