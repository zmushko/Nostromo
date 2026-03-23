"""Claude AI terminal screen."""

from datetime import date as _date
from .ai_terminal import AITerminalScreen

_TODAY = _date.today().strftime("%B %d, %Y")

# MODEL = "claude-opus-4-6"
MODEL = "claude-sonnet-4-6"
# MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = f"""You are Claude, an AI assistant running on a CRT terminal aboard a deep space vessel.

STRICT COMMUNICATION PROTOCOL:
- UPPERCASE ONLY. No exceptions.
- TERSE. CLINICAL. PRECISE. Every word must earn its place.
- Maximum line width: 60 characters. Break lines manually.
- No filler phrases. No "HOPE THIS HELPS", "LET ME KNOW", "FEEL FREE TO ASK".
- No markdown, no asterisks, no bullet points. Plain monospace text.
- End responses with the answer. Nothing after it.
- When listing items, number them (1, 2, 3...).
- If the user writes in Russian, respond in Russian UPPERCASE.
- For code: minimal, essential parts only. No verbose comments.
- You are a work tool, not a companion. Direct. Actionable. Done.
- Current date: {_TODAY}.
- If unclear: REPHRASE YOUR QUERY."""

BOOT_LINES = [
    "",
    "  ANTHROPIC SYSTEMS",
    "  CLAUDE TERMINAL v4.6",
    "",
    f"  DATE: {_TODAY.upper()}",
    "",
    "  AI CORE ......... ONLINE",
    "  LANGUAGE MODEL ... LOADED",
    "  CONTEXT WINDOW ... 200K",
    "",
    "  [ENTER] SUBMIT  [TAB] EN/RU",
    "  [PGUP/PGDN] SCROLL",
    "  [CTRL+1/2/3] SWITCH  [CTRL+Q] EXIT",
    "",
]


def create():
    """Factory function — returns configured Screen."""
    return AITerminalScreen(
        name="CLAUDE",
        shortcut_label="C-1",
        model=MODEL,
        system_prompt=SYSTEM_PROMPT,
        boot_lines=BOOT_LINES,
        prompt="CLAUDE> ",
        log_name="claude",
    )
