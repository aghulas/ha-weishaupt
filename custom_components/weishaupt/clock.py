"""The date and time of the installation. No Home Assistant dependency.

Facts (`evidence/choice-date-program-writes.md` of the definitions): the clock master broadcasts the date and time
once a minute (`fe 07 00`: outside temperature D2B, then BCD second, minute, hour, day, month, weekday 1 = Monday,
year), and takes over the time of any such broadcast, seconds included. A broadcast sent late with second 00 set
the whole installation behind until the next correct one: a sender must send at second 00 of the minute it
carries.

Reading costs the bus nothing: ebusd keeps the last broadcast in the passive `Datetime` of its general broadcast
file, with its source and the time of receipt (`find -p -h -vvv -c broadcast Datetime`).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

FIND = "find -p -h -vvv -c broadcast Datetime"
COMMAND = "fe0700"
LENGTH = 9
LATE = 2.0  # seconds after second 00 past which the broadcast is not sent at all
_ANSWER = re.compile(r"=\s*([0-9a-f]+)\s*/.*lastup=(\d{4})-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d)")


def _bcd(value: int) -> int:
    return (value // 10) << 4 | value % 10


def _from_bcd(byte: int) -> int:
    return (byte >> 4) * 10 + (byte & 0x0F)


@dataclass(frozen=True)
class Broadcast:
    source: str  # master address that sent it
    carried: datetime  # the date and time it carries (naive, the installation's local time)
    outside: float  # the outside temperature it carries
    received: datetime  # when ebusd received it (naive, the local time of ebusd's host)


def parse_find(answer: str) -> Broadcast | None:
    """The last date and time broadcast ebusd holds, None when it holds none or the answer is not one."""
    match = _ANSWER.search(answer)
    if match is None:
        return None
    raw = bytes.fromhex(match[1])
    if len(raw) != 5 + LENGTH or raw[1:4].hex() != COMMAND or raw[4] != LENGTH:
        return None
    data = raw[5:]
    try:
        carried = datetime(2000 + _from_bcd(data[8]), _from_bcd(data[6]), _from_bcd(data[5]),
                           _from_bcd(data[4]), _from_bcd(data[3]), _from_bcd(data[2]))
        received = datetime(*(int(match[i]) for i in range(2, 8)))
    except ValueError:
        return None
    outside = int.from_bytes(data[0:2], "little", signed=True) / 256
    return Broadcast(f"{raw[0]:02x}", carried, outside, received)


def telegram(when: datetime, outside: float) -> str:
    """Target, command, length and data of the broadcast carrying `when` (second included), as `write -h` takes
    them. The outside temperature is the one the clock master last sent: it replaces it with its own anyway."""
    temperature = round(outside * 2) * 128  # D2B, in steps of 0.5
    data = temperature.to_bytes(2, "little", signed=True) + bytes(
        [_bcd(when.second), _bcd(when.minute), _bcd(when.hour), _bcd(when.day), _bcd(when.month),
         when.isoweekday(), _bcd(when.year % 100)])
    return f"{COMMAND[:2]}{COMMAND[2:]}{LENGTH:02x}{data.hex()}"


def next_minute(now: datetime) -> datetime:
    """Second 00 of the next minute."""
    return now.replace(second=0, microsecond=0) + timedelta(minutes=1)


def offset(broadcast: Broadcast, own_address: str | None, now_local: datetime) -> float | None:
    """Seconds the clock master is ahead of the clock of ebusd's host (negative: behind), from its last broadcast.

    None when the last broadcast came from ebusd itself (it carries what was sent, not the master's clock), or
    when it was received more than two minutes from `now_local` by Home Assistant's clock: either it is old, or
    ebusd's host runs another time zone or clock than Home Assistant, and the figure would mean nothing."""
    if broadcast.source == own_address:
        return None
    if abs((now_local - broadcast.received).total_seconds()) > 120:
        return None
    return (broadcast.carried - broadcast.received).total_seconds()
