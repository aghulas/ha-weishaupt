"""Write guard, independent of the caller: every write goes through WriteGuard.check() before it is sent.

Not used by this version: the integration is read-only and nothing imports this module. It is kept, with its
tests, for the version that will write settings.

Rules:
- writes are refused unless enabled in the integration options;
- the value must be within the bounds of the register;
- at most one write per register every MIN_INTERVAL seconds and MAX_PER_HOUR writes in all per hour;
- a write from the service tool address ff is refused when WCM-Diagnose may be connected: a telegram from ff was
  logged during the last SERVICE_TOOL_QUIET seconds, outside of our own writes, or the telegram log cannot be read.
  Two masters with the same address would collide on the bus;
- a write from ff is also refused when the telegram log is not live, i.e. its newest telegram (any source) is older
  than LOG_FRESH_MAX seconds. The bus is chatty (a telegram every fraction of a second), so a stale newest means the
  add-on has stopped logging and the ff detector is blind — fail safe rather than write blind.
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
LOG_FRESH_MAX = 120.0


# Reasons of a refusal. The key is also the translation key of the message shown in Home Assistant
# (`exceptions` in the translations); the English text here is what the logs and the tests see.
REASONS = {
    "writes_disabled": "writes are disabled (integration options or write switch)",
    "out_of_bounds": "{value} is outside the bounds [{minimum}, {maximum}]",
    "hourly_limit": "more than {limit} writes within the hour",
    "register_interval": "this register was written less than {seconds} s ago",
    "clock_interval": "the clock was broadcast less than {seconds} s ago",
    "log_unreadable": "the telegram log cannot be read ({reason}): write from ff refused",
    "log_stale": "the telegram log is not being fed (no recent telegram): write from ff refused",
    "service_tool_active": "WCM-Diagnose seems to be connected (recent telegram from ff): write from ff refused",
}


class WriteRefused(Exception):
    """The guard refused the write; `code` says why (a key of REASONS), `placeholders` are its values."""

    def __init__(self, code: str, **placeholders: object) -> None:
        self.code = code
        self.placeholders = {key: str(value) for key, value in placeholders.items()}
        super().__init__(REASONS[code].format(**self.placeholders))


def read_service_tool_state(db_path: str) -> "ServiceToolState":
    """Read the add-on telegram log: time of the last ff telegram, and of the newest telegram of any source.

    `last_seen` detects WCM-Diagnose (address ff); `newest` tells whether the log is still being written. Our own
    ff writes are logged without their source byte (status 'invalid', qq NULL), so they never count as ff here."""
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5) as db:
        last_ff = db.execute("SELECT MAX(ts) FROM telegram WHERE qq = 255").fetchone()[0]
        newest = db.execute("SELECT MAX(ts) FROM telegram").fetchone()[0]
    return ServiceToolState(last_seen=last_ff / 1e9 if last_ff else None,
                            newest=newest / 1e9 if newest else None)


@dataclass(frozen=True)
class ServiceToolState:
    """What the telegram log says: time of the last ff telegram, time of the newest telegram (log liveness), or why
    it could not be read."""

    last_seen: float | None = None
    newest: float | None = None
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
            raise WriteRefused("writes_disabled")
        if not minimum <= value <= maximum:
            raise WriteRefused("out_of_bounds", value=value, minimum=minimum, maximum=maximum)
        now = self._clock()
        while self._writes and now - self._writes[0] > 3600:
            self._writes.popleft()
        if len(self._writes) >= MAX_PER_HOUR:
            raise WriteRefused("hourly_limit", limit=MAX_PER_HOUR)
        last = self._last_by_register.get(register_id)
        if last is not None and now - last < MIN_INTERVAL:
            raise WriteRefused("register_interval", seconds=f"{MIN_INTERVAL:.0f}")
        if source == "ff":
            self._check_service_tool(now, service_tool)

    def _check_service_tool(self, now: float, state: ServiceToolState | None) -> None:
        if state is None or state.error is not None:
            reason = state.error if state else "not read"
            raise WriteRefused("log_unreadable", reason=reason)
        if state.newest is None or now - state.newest > LOG_FRESH_MAX:
            raise WriteRefused("log_stale")
        seen = state.last_seen
        if seen is None or now - seen > SERVICE_TOOL_QUIET:
            return
        if any(abs(seen - own) <= OWN_WRITE_MARGIN for own in self._own_ff_writes):
            return
        raise WriteRefused("service_tool_active")

    def record(self, register_id: str, source: str | None) -> None:
        """To call right before sending a write the guard accepted."""
        now = self._clock()
        self._writes.append(now)
        self._last_by_register[register_id] = now
        if source == "ff":
            self._own_ff_writes.append(now)

    def check_broadcast(self) -> None:
        """Guard for the clock broadcast (fe 0700): enabled, not too soon, within the hourly rate limit.

        No bounds or ff check: it is a broadcast from ebusd's own address, not a register write."""
        if not self.enabled:
            raise WriteRefused("writes_disabled")
        now = self._clock()
        while self._writes and now - self._writes[0] > 3600:
            self._writes.popleft()
        if len(self._writes) >= MAX_PER_HOUR:
            raise WriteRefused("hourly_limit", limit=MAX_PER_HOUR)
        last = self._last_by_register.get("broadcast:clock")
        if last is not None and now - last < MIN_INTERVAL:
            raise WriteRefused("clock_interval", seconds=f"{MIN_INTERVAL:.0f}")

    def record_broadcast(self) -> None:
        """To call right before sending a clock broadcast the guard accepted."""
        now = self._clock()
        self._writes.append(now)
        self._last_by_register["broadcast:clock"] = now
