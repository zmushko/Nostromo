"""
Nostromo Terminal — shared configuration.
Colors, timing, screen dimensions, font settings.
"""

# Screen
SCREEN_W, SCREEN_H = 640, 480
FPS = 60

# CRT colors — phosphor green P1
COLOR_BG        = (0, 0, 0)
COLOR_TEXT       = (51, 255, 0)
COLOR_DIM        = (20, 100, 0)
COLOR_SCANLINE   = (0, 0, 0, 40)
COLOR_CURSOR     = (51, 255, 0)
COLOR_GLOW       = (30, 150, 0, 60)
COLOR_INPUT_DIM  = (15, 80, 0)
COLOR_BRIGHT     = (80, 255, 50)
COLOR_HIGHLIGHT  = (40, 200, 0)

# Video
VIDEO_SCALE = "fill"   # "fill" = crop edges, "fit" = black bars

# Screensaver
SCREENSAVER_MODE = "crab"     # "logo", "matrix", "status", "dvd", "crab", "off"
SCREENSAVER_TIMEOUT = 180     # seconds of idle before activation

# Font
FONT_SIZE = 17

# CRT effects
SCANLINES = False

# Sound
SOUND = True          # horizontal scanline overlay

# Timing
CHAR_DELAY_MS    = 30
CURSOR_BLINK_MS  = 530
BOOT_CHAR_DELAY  = 8

# Terminal geometry (set by app.init_display)
COLS = 63
ROWS = 20
INPUT_ROWS = 3
