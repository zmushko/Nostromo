"""
Nostromo Terminal — session logger.
Timestamped log files for any terminal application.
"""

import os
from datetime import datetime


class SessionLogger:
    """Logs terminal sessions to timestamped files."""

    def __init__(self, app_name="NOSTROMO", log_dir=None):
        if log_dir is None:
            # Default: logs/ next to the calling script
            log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = app_name.lower().replace(" ", "_")
        self.filepath = os.path.join(log_dir, f"{prefix}_{timestamp}.log")
        self.file = open(self.filepath, "w", encoding="utf-8")

        self._write(f"{app_name} SESSION LOG")
        self._write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._write("=" * 60)
        self._write("")

    def _write(self, text):
        self.file.write(text + "\n")
        self.file.flush()

    def log_event(self, label, text):
        """Log a generic event with timestamp."""
        ts = datetime.now().strftime("%H:%M:%S")
        self._write(f"[{ts}] {label}:")
        for line in text.split("\n"):
            self._write(f"  {line}")
        self._write("")

    def log_separator(self):
        self._write("-" * 60)
        self._write("")

    def log_query(self, query):
        self.log_event("CREW", query)

    def log_response(self, response):
        self.log_event("MOTHER", response)
        self.log_separator()

    def log_boot(self):
        self._write("[BOOT SEQUENCE COMPLETE]")
        self._write("")

    def log_raw(self, text):
        """Write raw text without formatting."""
        self._write(text)

    def close(self):
        self._write("")
        self._write(f"Session ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.file.close()
