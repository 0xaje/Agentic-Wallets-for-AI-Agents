"""
Styled console logger — emoji-coded on capable terminals, ASCII fallback on Windows cp1252.
"""

from __future__ import annotations

import io
import os
import sys
from datetime import datetime, timezone


def _supports_emoji() -> bool:
    """Detect whether stdout can encode emoji characters."""
    try:
        encoding = getattr(sys.stdout, "encoding", None) or "ascii"
        "\U0001f680".encode(encoding)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


# Emoji glyphs (used on UTF-8 terminals)
_EMOJI = {
    "info":    "\u2728",   "action":  "\U0001f680", "hydrate": "\U0001f4a7",
    "success": "\u2705",   "warn":    "\u26a0\ufe0f",  "error":   "\u274c",
    "boot":    "\U0001f916","seed":    "\U0001f331", "rain":    "\U0001f327\ufe0f",
    "target":  "\U0001f3af","key":     "\U0001f511", "shield":  "\U0001f6e1\ufe0f",
    "sweep":   "\U0001f9f9","loop":    "\U0001f504", "sleep":   "\U0001f634",
}

# ASCII fallback (used on cp1252 / non-UTF-8 consoles)
_ASCII = {
    "info":    "[..]", "action":  "[>>]", "hydrate": "[~~]",
    "success": "[OK]", "warn":    "[!!]", "error":   "[XX]",
    "boot":    "[^^]", "seed":    "[++]", "rain":    "[~~]",
    "target":  "[->]", "key":     "[**]", "shield":  "[::]",
    "sweep":   "[<<]", "loop":    "[<>]", "sleep":   "[zz]",
}


class AgentLogger:
    """Lightweight, level-coded logger with optional quiet mode."""

    def __init__(self, quiet: bool = False) -> None:
        self.quiet = quiet
        self._icons = _EMOJI if _supports_emoji() else _ASCII

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).strftime("%H:%M:%S")

    def _emit(self, level: str, msg: str, *, force: bool = False) -> None:
        if self.quiet and not force:
            return
        icon = self._icons.get(level, "[??]")
        line = f"[{self._timestamp()}] {icon}  {msg}"
        dest = sys.stderr if level in ("warn", "error") else sys.stdout
        print(line, file=dest)

    # -- Convenience shortcuts --
    def info(self, msg: str) -> None:
        self._emit("info", msg)

    def action(self, msg: str) -> None:
        self._emit("action", msg, force=True)

    def hydrate(self, msg: str) -> None:
        self._emit("hydrate", msg)

    def success(self, msg: str) -> None:
        self._emit("success", msg, force=True)

    def warn(self, msg: str) -> None:
        self._emit("warn", msg, force=True)

    def error(self, msg: str) -> None:
        self._emit("error", msg, force=True)

    def boot(self, msg: str) -> None:
        self._emit("boot", msg, force=True)

    def seed(self, msg: str) -> None:
        self._emit("seed", msg)

    def rain(self, msg: str) -> None:
        self._emit("rain", msg)

    def target(self, msg: str) -> None:
        self._emit("target", msg, force=True)

    def key(self, msg: str) -> None:
        self._emit("key", msg)

    def shield(self, msg: str) -> None:
        self._emit("shield", msg)

    def sweep(self, msg: str) -> None:
        self._emit("sweep", msg)

    def loop(self, msg: str) -> None:
        self._emit("loop", msg)

    def sleep(self, msg: str) -> None:
        self._emit("sleep", msg)
