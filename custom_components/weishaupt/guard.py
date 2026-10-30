"""Write guard, outside of any LLM: every write goes through WriteGuard.check() before it is sent.

Rules:
- writes are refused unless enabled in the integration options;
- the value must be within the bounds of the register;
- at most one write per register every MIN_INTERVAL seconds and MAX_PER_HOUR writes in all per hour;
- a write from the service tool address ff is refused when WCM-Diagnose may be connected: a telegram from ff was
  logged during the last SERVICE_TOOL_QUIET seconds, outside of our own writes, or the telegram log cannot be read.
  Two masters with the same address would collide on the bus.
"""
from __future__ import annotations

import sqlite3
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

MIN_INTERVAL = 10.0
MAX_PER_HOUR = 30
SERVICE_TOOL_QUIET = 600.0
OWN_WRITE_MARGIN = 5.0


class WriteRefused(Exception):
    """The guard refused the write; the message says why (shown to the user)."""


def last_service_tool_telegram(db_path: str) -> float | None:
    """Time (s since epoch) of the last telegram from ff in the ebusd telegram log of the add-on, None if none."""
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5) as db:
        row = db.execute("SELECT MAX(ts) FROM telegram WHERE qq = 255").fetchone()
    return row[0] / 1e9 if row and row[0] else None


@dataclass(frozen=True)
class ServiceToolState:
    """What the telegram log says about ff: time of its last telegram (None = never), or why it could not be read."""

    last_seen: float | None = None
    error: str | None = None


class WriteGuard:
    def __init__(self, enabled: bool, clock: Callable[[], float] = time.time) -> None:
        self.enabled = enabled
        self._clock = clock
        self._writes: deque[float] = deque()
        self._last_by_register: dict[str, float] = {}
        self._own_ff_writes: deque[float] = deque(maxlen=200)

    def check(self, register_id: str, value: float, minimum: float, maximum: float, source: str | None,
              service_tool: ServiceToolState | None = None) -> None:
        if not self.enabled:
            raise WriteRefused("écritures désactivées dans les options de l'intégration")
        if not minimum <= value <= maximum:
            raise WriteRefused(f"{value} hors des bornes [{minimum}, {maximum}]")
        now = self._clock()
        while self._writes and now - self._writes[0] > 3600:
            self._writes.popleft()
        if len(self._writes) >= MAX_PER_HOUR:
            raise WriteRefused(f"plus de {MAX_PER_HOUR} écritures dans l'heure")
        last = self._last_by_register.get(register_id)
        if last is not None and now - last < MIN_INTERVAL:
            raise WriteRefused(f"une écriture de ce registre il y a moins de {MIN_INTERVAL:.0f} s")
        if source == "ff":
            self._check_service_tool(now, service_tool)

    def _check_service_tool(self, now: float, state: ServiceToolState | None) -> None:
        if state is None or state.error is not None:
            reason = state.error if state else "non consulté"
            raise WriteRefused(f"journal des trames illisible ({reason}) : écriture depuis ff refusée")
        seen = state.last_seen
        if seen is None or now - seen > SERVICE_TOOL_QUIET:
            return
        if any(abs(seen - own) <= OWN_WRITE_MARGIN for own in self._own_ff_writes):
            return
        raise WriteRefused("WCM-Diagnose semble connecté (trame de ff récente) : écriture depuis ff refusée")

    def record(self, register_id: str, source: str | None) -> None:
        """To call right before sending a write the guard accepted."""
        now = self._clock()
        self._writes.append(now)
        self._last_by_register[register_id] = now
        if source == "ff":
            self._own_ff_writes.append(now)
