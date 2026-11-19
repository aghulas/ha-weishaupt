"""Write guard, independent of Home Assistant: every write goes through WriteGuard.check() before it is sent.

Carried over from version 0.1, where it was proven in service. Rules:
- writes are refused unless enabled (integration options and the write switch);
- the value must lie within the bounds of the setting, narrowed by the linked settings;
- at most one write per register every MIN_INTERVAL seconds, and at most `max_per_hour` writes in all per hour:
  the option `max_writes_per_hour` of the entry, MAX_PER_HOUR by default, accepted within MAX_PER_HOUR_RANGE (as in
  0.1.2). The limit spares the memory of the devices; a high value is for a supervised test campaign;
- a write from the address of the vendor service tool (ff) is refused when the tool may be connected: a telegram
  from ff was logged during the last SERVICE_TOOL_QUIET seconds, outside of our own writes, or the telegram log
  cannot be read. Two masters with the same address would collide on the bus;
- a write from ff is also refused when the telegram log is not live, i.e. its newest telegram (any source) is
  older than LOG_FRESH_MAX seconds. The bus is chatty (a telegram every fraction of a second), so a stale newest
  means the log is no longer written and the ff detector is blind: fail safe rather than write blind.

The telegram log is the SQLite file the ebusd add-on of the test installation keeps (table `telegram`, columns `ts`
in nanoseconds and `qq`). Our own writes from ff are logged without their source byte (qq NULL), so they never
count as ff; OWN_WRITE_MARGIN covers a log that would store it.
"""
from __future__ import annotations

import math
import sqlite3
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

MIN_INTERVAL = 10.0
MAX_PER_HOUR = 30
MAX_PER_HOUR_RANGE = (1, 200)
SERVICE_TOOL_QUIET = 600.0
OWN_WRITE_MARGIN = 5.0
LOG_FRESH_MAX = 120.0


# Reasons of a refusal. The key is also the translation key of the message shown in Home Assistant
# (`exceptions` in the translations); the English text here is what the logs and the tests see.
REASONS = {
    "writes_disabled": "writes are disabled (integration options or write switch)",
    "not_writable": "{setting} is not writable: {reason}",
    "capability_absent": "ebusd does not compute the run-time checksum (john30/ebusd#1825): writes refused",
    "capability_unknown": "whether ebusd computes the run-time checksum is not known ({reason}): writes refused",
    "source_not_own": "{setting} is proven written from address 31 only, and ebusd's own address is {own}",
    "off_step": "{value} is not on a step of {step} from {minimum}",
    "out_of_bounds": "{value} is outside the bounds [{minimum}, {maximum}]",
    "linked_unknown": "{other} could not be read: write refused",
    "hourly_limit": "more than {limit} writes within the hour",
    "register_interval": "this register was written less than {seconds} s ago",
    "log_unreadable": "the telegram log cannot be read ({reason}): write from ff refused",
    "log_stale": "the telegram log is not being fed (no recent telegram): write from ff refused",
    "service_tool_active": "the vendor service tool seems to be connected (recent telegram from ff): write from "
                           "ff refused",
    "read_failed": "{setting} could not be read before the write ({reason}): write refused",
    "unavailable": "ebusd cannot be reached: write refused",
    "bad_day_format": "{day}: {part!r} is not a range; expected up to 3 ranges like 06:30-18:00, 19:00-21:00, or -",
    "bad_day_quarter": "{day}: {part}: times are quarters of an hour, 00:00 to 24:00",
    "bad_day_order": "{day}: {part}: the start must be before the end",
    "bad_day_too_many": "{day}: at most 3 ranges a day",
    "bad_day_overlap": "{day}: the ranges overlap",
    "program_limit": "{needed} slots to write and {left} writes left within the hour (limit {limit}): nothing written",
}


class WriteRefused(Exception):
    """The guard refused the write; `code` says why (a key of REASONS), `placeholders` are its values."""

    def __init__(self, code: str, **placeholders: object) -> None:
        self.code = code
        self.placeholders = {key: str(value) for key, value in placeholders.items()}
        super().__init__(REASONS[code].format(**self.placeholders))


def hourly_limit(value: object) -> int:
    """The hourly write limit from the option value: MAX_PER_HOUR when unset, a valid integer as is.

    Raises ValueError for anything else (not an integer, or outside MAX_PER_HOUR_RANGE)."""
    if value is None:
        return MAX_PER_HOUR
    if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
        raise ValueError(f"not an integer: {value!r}")
    low, high = MAX_PER_HOUR_RANGE
    if not low <= int(value) <= high:
        raise ValueError(f"{value} is outside {low} to {high}")
    return int(value)


def read_service_tool_state(db_path: str) -> "ServiceToolState":
    """Read the telegram log: time of the last ff telegram, and of the newest telegram of any source.

    `last_seen` detects the vendor service tool (address ff); `newest` tells whether the log is still written."""
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5) as db:
            last_ff = db.execute("SELECT MAX(ts) FROM telegram WHERE qq = 255").fetchone()[0]
            newest = db.execute("SELECT MAX(ts) FROM telegram").fetchone()[0]
    except sqlite3.Error as err:
        return ServiceToolState(error=str(err))
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
    def __init__(self, enabled: bool, clock: Callable[[], float] = time.time,
                 max_per_hour: int = MAX_PER_HOUR) -> None:
        self.enabled = enabled
        self.max_per_hour = hourly_limit(max_per_hour)
        self._clock = clock
        self._writes: deque[float] = deque()
        self._last_by_register: dict[str, float] = {}
        self._own_ff_writes: deque[float] = deque(maxlen=200)

    def check(self, register_id: str, value: float, minimum: float, maximum: float, source: str | None,
              service_tool: ServiceToolState | None = None) -> None:
        if not self.enabled:
            raise WriteRefused("writes_disabled")
        if math.isnan(value) or not minimum <= value <= maximum:
            raise WriteRefused("out_of_bounds", value=value, minimum=minimum, maximum=maximum)
        now = self._clock()
        while self._writes and now - self._writes[0] > 3600:
            self._writes.popleft()
        if len(self._writes) >= self.max_per_hour:
            raise WriteRefused("hourly_limit", limit=self.max_per_hour)
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

    def writes_last_hour(self) -> int:
        now = self._clock()
        return sum(1 for when in self._writes if now - when <= 3600)
