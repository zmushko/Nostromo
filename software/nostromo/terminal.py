"""
Nostromo Terminal — base terminal engine.
Boot sequence, text input with wrapping, scrollback, cursor.
Command history with persistence.
Subclass or compose to build applications.
"""

import os
import pygame
from . import config as cfg
from . import sound
from .crt import CRTRenderer
from .keyboard import KeyboardLayout


HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "history")
HISTORY_MAX = 100


class BaseTerminal:
    """Base terminal with boot sequence, input, scrollback, scrolling.

    Subclasses should override:
        on_submit(query)  — called when user presses Enter
        on_boot_complete() — called when boot sequence finishes
    """

    def __init__(self, renderer, boot_lines=None, prompt="INPUT> ",
                 input_rows=None, history_name=None):
        self.renderer = renderer
        self.prompt = prompt
        self.input_rows = input_rows or cfg.INPUT_ROWS

        # State
        self.booting = bool(boot_lines)
        self.idle = not self.booting
        self.busy = False  # set by subclass when processing

        # Display buffer (scrollback)
        self.lines = []
        self.max_lines = 2000
        self.scroll_offset = 0

        # Input
        self.input_buf = ""
        self.keyboard = KeyboardLayout()

        # Command history
        self._history_name = history_name
        self._history = []
        self._history_idx = -1     # -1 = not browsing history
        self._history_stash = ""   # saves current input when browsing
        if history_name:
            self._load_history()

        # Cursor blink
        self.cursor_visible = True
        self._last_cursor_toggle = 0

        # Boot sequence
        self._boot_lines = list(boot_lines) if boot_lines else []
        self._boot_index = 0
        self._boot_char_index = 0
        self._boot_current_line = ""
        self._last_char_time = 0

        # Working indicator
        self._working_dots = 0
        self._last_dot_time = 0

    # ─── Properties ─────────────────────────────────────────────────────

    @property
    def _current_input_display_rows(self):
        """How many screen rows the current input occupies."""
        if not self.idle:
            return 0
        return len(self._wrap_input(self.input_buf))

    @property
    def output_rows(self):
        """Rows available for scrollback text."""
        if not self.idle:
            return cfg.ROWS + self.input_rows
        return cfg.ROWS + self.input_rows - self._current_input_display_rows

    @property
    def first_input_row(self):
        """Screen row where input area starts."""
        return self.output_rows + 1

    # ─── Display buffer ─────────────────────────────────────────────────

    def add_line(self, text):
        """Add a line to scrollback, with word-wrapping."""
        while len(text) > cfg.COLS:
            wrap = text[:cfg.COLS].rfind(' ')
            if wrap <= 0:
                wrap = cfg.COLS
            self.lines.append(text[:wrap])
            text = text[wrap:].lstrip()
        self.lines.append(text)

        if len(self.lines) > self.max_lines:
            self.lines = self.lines[-self.max_lines:]

    def _get_visible_lines(self, count):
        """Get lines for display, respecting scroll offset."""
        end = len(self.lines) - self.scroll_offset
        start = max(0, end - count)
        return self.lines[start:end]

    # ─── Input wrapping ─────────────────────────────────────────────────

    def _wrap_input(self, text):
        """Wrap input buffer into display lines with prompt/continuation."""
        first_width = cfg.COLS - len(self.prompt)
        cont_width = cfg.COLS - 2  # "> " prefix
        lines = []
        if len(text) <= first_width:
            lines.append(self.prompt + text)
        else:
            lines.append(self.prompt + text[:first_width])
            rest = text[first_width:]
            while rest:
                chunk = rest[:cont_width]
                rest = rest[cont_width:]
                lines.append("> " + chunk)
        return lines

    def _max_input_chars(self):
        """Maximum characters that fit in input area."""
        first_width = cfg.COLS - len(self.prompt)
        cont_width = cfg.COLS - 2
        return first_width + cont_width * (self.input_rows - 1)

    # ─── Command history ────────────────────────────────────────────────

    def _history_file(self):
        """Path to history file for this terminal."""
        if not self._history_name:
            return None
        return os.path.join(HISTORY_DIR, f"{self._history_name}.hist")

    def _load_history(self):
        """Load history from disk."""
        path = self._history_file()
        if not path or not os.path.exists(path):
            return
        try:
            with open(path, "r") as f:
                self._history = [
                    line.strip() for line in f.readlines()
                    if line.strip()
                ][-HISTORY_MAX:]
        except Exception:
            pass

    def _save_history(self):
        """Save history to disk."""
        path = self._history_file()
        if not path:
            return
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                for entry in self._history[-HISTORY_MAX:]:
                    f.write(entry + "\n")
        except Exception:
            pass

    def _history_add(self, query):
        """Add a query to history (skip duplicates of last entry)."""
        if not query:
            return
        if self._history and self._history[-1] == query:
            return
        self._history.append(query)
        if len(self._history) > HISTORY_MAX:
            self._history = self._history[-HISTORY_MAX:]
        self._save_history()

    def _history_up(self):
        """Navigate to previous history entry."""
        if not self._history:
            return
        if self._history_idx == -1:
            # Starting to browse — stash current input
            self._history_stash = self.input_buf
            self._history_idx = len(self._history) - 1
        elif self._history_idx > 0:
            self._history_idx -= 1
        else:
            return  # already at oldest
        self.input_buf = self._history[self._history_idx]

    def _history_down(self):
        """Navigate to next history entry, or back to stashed input."""
        if self._history_idx == -1:
            return  # not browsing
        if self._history_idx < len(self._history) - 1:
            self._history_idx += 1
            self.input_buf = self._history[self._history_idx]
        else:
            # Back to current input
            self._history_idx = -1
            self.input_buf = self._history_stash
            self._history_stash = ""

    def _history_reset(self):
        """Reset history browsing state."""
        self._history_idx = -1
        self._history_stash = ""

    # ─── Callbacks (override in subclass) ───────────────────────────────

    def on_submit(self, query):
        """Called when user submits input. Override in subclass."""
        pass

    def on_boot_complete(self):
        """Called when boot sequence finishes. Override in subclass."""
        pass

    # ─── Input handling ─────────────────────────────────────────────────

    def submit(self):
        """Process input submission."""
        query = self.input_buf.strip()
        if not query:
            return

        self.scroll_offset = 0

        # Echo input
        for vline in self._wrap_input(self.input_buf):
            self.add_line(vline)
        self.add_line("")

        # Save to history and reset browsing
        self._history_add(query)
        self._history_reset()

        self.input_buf = ""
        self.on_submit(query)

    def handle_key(self, event):
        """Process a KEYDOWN event. Returns True if handled."""
        # Scrolling — works in any state
        if event.key == pygame.K_PAGEUP:
            self.scroll_offset = min(
                self.scroll_offset + self.output_rows // 2,
                max(0, len(self.lines) - self.output_rows)
            )
            return True
        elif event.key == pygame.K_PAGEDOWN:
            self.scroll_offset = max(
                0, self.scroll_offset - self.output_rows // 2
            )
            return True
        elif event.key == pygame.K_HOME:
            self.scroll_offset = max(0, len(self.lines) - self.output_rows)
            return True
        elif event.key == pygame.K_END:
            self.scroll_offset = 0
            return True

        # Text input — only when idle
        if not self.idle:
            return False

        if event.key == pygame.K_RETURN:
            self.submit()
            return True

        elif event.key == pygame.K_UP:
            self._history_up()
            return True

        elif event.key == pygame.K_DOWN:
            self._history_down()
            return True

        elif event.key == pygame.K_BACKSPACE:
            if self.input_buf:
                self.input_buf = self.input_buf[:-1]
            return True

        elif event.key == pygame.K_ESCAPE:
            self.input_buf = ""
            self._history_reset()
            return True

        elif event.key == pygame.K_TAB:
            self.keyboard.toggle()
            return True

        elif event.unicode and event.unicode.isprintable():
            ch = self.keyboard.translate(event.unicode).upper()
            if len(self.input_buf) < self._max_input_chars():
                self.input_buf += ch
            return True

        return False

    # ─── Update ─────────────────────────────────────────────────────────

    def update(self):
        """Call once per frame."""
        now = pygame.time.get_ticks()

        # Cursor blink
        if now - self._last_cursor_toggle > cfg.CURSOR_BLINK_MS:
            self.cursor_visible = not self.cursor_visible
            self._last_cursor_toggle = now

        # Boot sequence
        if self.booting:
            self._update_boot(now)

    def _update_boot(self, now):
        if self._boot_index >= len(self._boot_lines):
            self.add_line("")
            self.booting = False
            self.idle = True
            self.on_boot_complete()
            return

        if now - self._last_char_time < cfg.BOOT_CHAR_DELAY:
            return

        line = self._boot_lines[self._boot_index]

        if self._boot_char_index >= len(line):
            self.add_line(self._boot_current_line)
            self._boot_current_line = ""
            self._boot_index += 1
            self._boot_char_index = 0
            self._last_char_time = now + 30
            sound.play_line_pip()
            return

        self._boot_current_line += line[self._boot_char_index]
        self._boot_char_index += 1
        self._last_char_time = now
        sound.play_tick()

    # ─── Rendering ──────────────────────────────────────────────────────

    def set_busy(self, busy):
        """Set busy state (hides input, shows WORKING...)."""
        self.busy = busy
        self.idle = not busy

    def show_working(self):
        """Update and render the WORKING... indicator."""
        now = pygame.time.get_ticks()
        if now - self._last_dot_time > 500:
            self._working_dots = (self._working_dots + 1) % 4
            self._last_dot_time = now
        dots = "." * self._working_dots
        self.renderer.render_text_line(
            f"  WORKING{dots}", self.output_rows - 1, cfg.COLOR_DIM
        )

    def render(self):
        """Render the terminal. Call after screen.fill(BG)."""
        r = self.renderer

        if self.booting:
            # Top-aligned during boot
            visible = self._get_visible_lines(self.output_rows)
            for i, line in enumerate(visible):
                r.render_text_line(line, i)
            if self._boot_current_line:
                row = len(visible)
                if row < self.output_rows:
                    r.render_text_line(self._boot_current_line, row)
                    r.draw_cursor(
                        len(self._boot_current_line), row,
                        self.cursor_visible
                    )
            return

        # Scrollback — bottom-aligned
        visible = self._get_visible_lines(self.output_rows)
        for i, line in enumerate(visible):
            row = self.output_rows - len(visible) + i
            r.render_text_line(line, row)

        # Scroll indicator
        if self.scroll_offset > 0:
            indicator = f"[+{self.scroll_offset}]"
            indicator_col = cfg.COLS - len(indicator) - 1
            for i, ch in enumerate(indicator):
                r.render_char(ch, indicator_col + i, 0, cfg.COLOR_DIM)

        # Input area — only when idle
        if self.idle:
            r.draw_separator(self.first_input_row)

            # Wrapped input text
            wrapped = self._wrap_input(self.input_buf)
            for i, vline in enumerate(wrapped):
                r.render_text_line(vline, self.first_input_row + i)

            # Cursor position
            first_width = cfg.COLS - len(self.prompt)
            buf_len = len(self.input_buf)
            if buf_len <= first_width:
                crow = self.first_input_row
                ccol = len(self.prompt) + buf_len
            else:
                cont_width = cfg.COLS - 2
                overflow = buf_len - first_width
                line_idx = 1 + overflow // cont_width
                col_in_line = overflow % cont_width
                crow = self.first_input_row + line_idx
                ccol = 2 + col_in_line
            r.draw_cursor(ccol, crow, self.cursor_visible)

            # Layout indicator
            label = self.keyboard.label
            icol = cfg.COLS - 3
            color = cfg.COLOR_TEXT if self.keyboard.is_ru else cfg.COLOR_DIM
            for i, ch in enumerate(label):
                r.render_char(ch, icol + i, self.first_input_row, color)
