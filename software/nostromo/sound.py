"""
Nostromo Terminal — sound synthesis.
Generates CRT terminal sounds programmatically.
Inspired by the MU-TH-UR 6000 terminal in Alien (1979).
"""

import numpy as np
import pygame
from . import config as cfg

# Mixer settings
SAMPLE_RATE = 22050
CHANNELS = 1

_initialized = False
_sounds = {}


def init():
    """Initialize sound system."""
    global _initialized
    if not cfg.SOUND or _initialized:
        return

    try:
        pygame.mixer.pre_init(SAMPLE_RATE, -16, CHANNELS, 256)
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        _generate_sounds()
        _initialized = True
    except Exception as e:
        print(f"[sound] init failed: {e}")


def _generate_sounds():
    """Synthesize all terminal sounds."""
    _sounds['tick'] = _make_tick(freq=3000)
    _sounds['tick_alt'] = _make_tick(freq=2700)
    _sounds['line_pip'] = _make_line_pip()


def _make_tick(freq=3000, duration=0.06):
    """
    Filtered noise burst — dot matrix / CRT character sound.
    Short noise shaped by resonant frequency, fast decay.
    """
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)

    env = np.exp(-t * 600)
    noise = np.random.uniform(-1, 1, n).astype(np.float32)
    # Bandpass via resonant sine modulation
    signal = noise * np.sin(2 * np.pi * freq * t) * env * 0.00

    return _to_sound(signal)


def _make_line_pip(duration=0.100):
    """
    End-of-line pip — bright major chord at 3kHz.
    """
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)

    env = np.exp(-t * 30)

    root = 1800
    third = root * 1.26
    fifth = root * 1.5

    chord = (
        np.sin(2 * np.pi * root * t) * 0.5 +
        np.sin(2 * np.pi * third * t) * 0.35 +
        np.sin(2 * np.pi * fifth * t) * 0.25
    )

    signal = chord * env * 0.07

    return _to_sound(signal)


def _to_sound(signal):
    """Convert float32 numpy array to pygame.mixer.Sound."""
    # Clip and convert to int16
    signal = np.clip(signal, -1.0, 1.0)
    pcm = (signal * 32767).astype(np.int16)
    return pygame.mixer.Sound(buffer=pcm.tobytes())


# ─── Public API ─────────────────────────────────────────────────────────────

_tick_toggle = False

def play_tick():
    """Play typewriter tick (alternates between two variants)."""
    global _tick_toggle
    if not _initialized:
        return
    name = 'tick_alt' if _tick_toggle else 'tick'
    _tick_toggle = not _tick_toggle
    _sounds[name].play()


def play_line_pip():
    """Play end-of-line major chord pip."""
    if not _initialized:
        return
    _sounds['line_pip'].play()


def quit():
    """Release sound resources."""
    global _initialized
    _sounds.clear()
    _initialized = False
