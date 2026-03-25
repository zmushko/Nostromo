"""
AI Terminal Screen — common base for Claude and Mother.
Handles Claude API streaming, typewriter output, scrollback.
"""

import os
import sys
import queue
import threading
import pygame
import anthropic

from nostromo.screen import Screen
from nostromo.terminal import BaseTerminal
from nostromo.logger import SessionLogger
from nostromo import config as cfg
from nostromo import sound


class AIBrain:
    """Claude API client with streaming and history."""

    def __init__(self, model, system_prompt):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.system_prompt = system_prompt
        self.history = []

    def query(self, user_input, output_queue):
        self.history.append({"role": "user", "content": user_input})

        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=self.history,
            ) as stream:
                full_response = []
                for text in stream.text_stream:
                    full_response.append(text)
                    output_queue.put(text)

            response_text = "".join(full_response)
            self.history.append({"role": "assistant", "content": response_text})

            if len(self.history) > 40:
                self.history = self.history[-40:]

        except Exception as e:
            output_queue.put(e)

        output_queue.put(None)


class AITerminal(BaseTerminal):
    """Terminal with Claude API typewriter output."""

    def __init__(self, renderer, brain, logger, boot_lines, prompt,
                 history_name=None):
        super().__init__(renderer, boot_lines=boot_lines, prompt=prompt,
                         history_name=history_name)
        self.brain = brain
        self.logger = logger

        # Typewriter
        self._output_queue = queue.Queue()
        self._char_queue = []
        self._last_char_time = 0
        self._char_delay = cfg.CHAR_DELAY_MS
        self._partial_line = ""
        self._response_buffer = []

        # States
        self._waiting = False
        self._printing = False

    def on_boot_complete(self):
        self.logger.log_boot()

    def on_submit(self, query):
        self.logger.log_query(query)
        self._response_buffer = []
        self._waiting = True
        self._printing = False
        self.set_busy(True)
        self._working_dots = 0
        self._last_dot_time = pygame.time.get_ticks()

        thread = threading.Thread(
            target=self.brain.query,
            args=(query, self._output_queue),
            daemon=True,
        )
        thread.start()

    def _finish_response(self):
        partial = self._partial_line
        if partial:
            self.add_line(partial)
            self._partial_line = ""
        self.add_line("")
        self._waiting = False
        self._printing = False
        self.set_busy(False)
        self.logger.log_response("".join(self._response_buffer))

    def _drain_api_queue(self):
        while True:
            try:
                item = self._output_queue.get_nowait()
            except queue.Empty:
                break

            if item is None:
                if not self._char_queue:
                    self._finish_response()
                else:
                    self._char_queue.append(None)
                break
            elif isinstance(item, Exception):
                self.add_line(f"  SYSTEM ERROR: {item}")
                self.add_line("")
                self._waiting = False
                self._printing = False
                self.set_busy(False)
                break
            else:
                self._response_buffer.append(item)
                for ch in item:
                    self._char_queue.append(ch)
                if self._waiting:
                    self._waiting = False
                    self._printing = True
                    self._char_delay = cfg.CHAR_DELAY_MS

    def _process_char_queue(self, now):
        if not self._char_queue:
            return
        if now - self._last_char_time < self._char_delay:
            return

        ch = self._char_queue.pop(0)

        if ch is None:
            self._finish_response()
            return

        if ch == '\n':
            self.add_line(self._partial_line)
            self._partial_line = ""
            sound.play_line_pip()
        else:
            self._partial_line += ch
            sound.play_tick()

        self._last_char_time = now

    def update(self):
        super().update()
        if self._waiting or self._printing:
            self._drain_api_queue()
            self._process_char_queue(pygame.time.get_ticks())

    def render(self):
        r = self.renderer

        if self.booting:
            super().render()
            return

        if self._printing:
            partial = self._partial_line
            if partial:
                visible = self._get_visible_lines(self.output_rows - 1)
                for i, line in enumerate(visible):
                    row = self.output_rows - 1 - len(visible) + i
                    r.render_text_line(line, row)
                r.render_text_line(partial, self.output_rows - 1)
            else:
                visible = self._get_visible_lines(self.output_rows)
                for i, line in enumerate(visible):
                    row = self.output_rows - len(visible) + i
                    r.render_text_line(line, row)

        elif self._waiting:
            visible = self._get_visible_lines(self.output_rows - 1)
            for i, line in enumerate(visible):
                row = self.output_rows - 1 - len(visible) + i
                r.render_text_line(line, row)
            self.show_working()

        else:
            super().render()
            return

        if self.scroll_offset > 0:
            indicator = f"[+{self.scroll_offset}]"
            icol = cfg.COLS - len(indicator) - 1
            for i, ch in enumerate(indicator):
                r.render_char(ch, icol + i, 0, cfg.COLOR_DIM)


class AITerminalScreen(Screen):
    """Screen adapter for AI terminal (Claude/Mother/etc)."""

    def __init__(self, name, shortcut_label, model, system_prompt,
                 boot_lines, prompt, log_name):
        super().__init__(name, shortcut_label)
        self.model = model
        self.system_prompt = system_prompt
        self.boot_lines = boot_lines
        self.prompt = prompt
        self.log_name = log_name
        self.terminal = None
        self.brain = None
        self.logger = None

    def init(self, renderer):
        super().init(renderer)
        self.brain = AIBrain(self.model, self.system_prompt)
        self.logger = SessionLogger(app_name=self.log_name)
        self.terminal = AITerminal(
            renderer, self.brain, self.logger,
            self.boot_lines, self.prompt,
            history_name=self.log_name,
        )
        print(f"[{self.name}] logging to: {self.logger.filepath}",
              file=sys.stderr)

    def handle_event(self, event):
        if self.terminal and event.type == pygame.KEYDOWN:
            return self.terminal.handle_key(event)
        return False

    def update(self):
        if self.terminal:
            self.terminal.update()

    def render(self):
        if self.terminal:
            self.terminal.render()

    def is_alive(self):
        # AI terminal needs update when waiting for API response
        if self.terminal:
            return self.terminal._waiting or self.terminal._printing
        return False

    def cleanup(self):
        if self.logger:
            self.logger.close()
