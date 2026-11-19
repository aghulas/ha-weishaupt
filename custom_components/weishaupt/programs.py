"""Weekly programs: one day of a program as text, its three slots as register values. No Home Assistant dependency.

A program has 7 days of 3 slots; each slot is one 16-bit register (`<day << 4 | slot - 1> <program code>`, e.g.
`72 14` = Sunday slot 3 of heating program 1), read and written like the settings (`50 22` / `50 23`, run-time
checksum). Its two bytes, low first, are the end and the start of the slot: each a time in quarters of an hour
(TTQ, 7 bits) and a flag in bit 7 (BI7, 0 = enabled). `48 1a` is 06:30-18:00; an unused slot is `80 80`
(`evidence/room-units-programs.md` and `evidence/choice-date-program-writes.md` of the definitions).

The text of a day is what the program sensors already show: `06:30-18:00, 19:00-21:00`, up to three ranges in
quarters of an hour, `-` for none. A slot with only one of its two flags enabled is shown as unused, and is
rewritten unused when its day is written.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .ebusd import Definition
from .model import Model
from .writes import PBSB, WCRC_MARKER, WriteSpec

SLOTS = 3
UNUSED = 0x8080
QUARTERS_PER_DAY = 96
_RANGE = re.compile(r"^(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})$")
# what a text entity accepts, before the checks of `parse_day`
PATTERN = r"^\s*(-|(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})(\s*,\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}){0,2})?\s*$"
MAX_LENGTH = 100  # room for a wrong entry, so that the integration explains it rather than a length error


class DayError(ValueError):
    """The text of a day is not up to three ranges in quarters of an hour. `code` says why (the key of the message
    shown to the user, `bad_day_<code>` in the translations), `part` the range at fault."""

    def __init__(self, code: str, part: str = "") -> None:
        self.code, self.part = code, part.strip()
        super().__init__(f"{code}: {self.part}" if self.part else code)


def _quarter(hours: str, minutes: str, text: str) -> int:
    h, m = int(hours), int(minutes)
    if m % 15 or m > 45 or h > 24 or (h == 24 and m):
        raise DayError("quarter", text)
    return h * 4 + m // 15


def parse_day(text: str) -> list[tuple[int, int]]:
    """`06:30-18:00, 19:00-21:00` -> [(26, 72), (76, 84)] in quarters of an hour; `-` or nothing -> []."""
    text = text.strip()
    if text in ("", "-"):
        return []
    ranges = []
    for part in text.split(","):
        match = _RANGE.match(part.strip())
        if match is None:
            raise DayError("format", part)
        start = _quarter(match[1], match[2], part)
        end = _quarter(match[3], match[4], part)
        if start >= end:
            raise DayError("order", part)
        ranges.append((start, end))
    if len(ranges) > SLOTS:
        raise DayError("too_many")
    ranges.sort()
    for (_, end), (start, _) in zip(ranges, ranges[1:]):
        if start < end:
            raise DayError("overlap")
    return ranges


def _time(quarter: int) -> str:
    return f"{quarter // 4:02d}:{quarter % 4 * 15:02d}"


def format_day(ranges: list[tuple[int, int]]) -> str:
    return ", ".join(f"{_time(s)}-{_time(e)}" for s, e in ranges) or "-"


def slot_raw(slot: tuple[int, int] | None) -> int:
    """Register value of a slot: end (low byte), start (high byte), bit 7 clear when enabled."""
    if slot is None:
        return UNUSED
    start, end = slot
    return end | start << 8


def raws_of_day(ranges: list[tuple[int, int]]) -> list[int]:
    """The three register values of a day: its ranges in order, then unused slots."""
    return [slot_raw(ranges[i] if i < len(ranges) else None) for i in range(SLOTS)]


def range_of_raw(raw: int) -> tuple[int, int] | None:
    """A slot as a range, None when unused (either flag disabled)."""
    end, start = raw & 0xFF, raw >> 8
    if end & 0x80 or start & 0x80:
        return None
    return (start, end)


def raw_of_fields(values: tuple[str, ...]) -> int | None:
    """Register value of a slot from what ebusd answers to its read: `totime;toenabled;fromtime;fromenabled`."""
    if len(values) != 4:
        return None
    try:
        to_q = _quarter(*values[0].split(":"), values[0])
        from_q = _quarter(*values[2].split(":"), values[2])
    except (DayError, TypeError, ValueError):
        return None
    flags = {"Enabled": 0, "Disabled": 0x80}
    if values[1] not in flags or values[3] not in flags:
        return None
    return (to_q | flags[values[1]]) | (from_q | flags[values[3]]) << 8


@dataclass(frozen=True)
class SlotSpec(WriteSpec):
    """A program slot, written as its 16-bit register value (the value of `raw` is the register value)."""

    def raw(self, value: float) -> int:
        raw = int(value)
        if not 0 <= raw <= 0xFFFF:
            raise ValueError(f"{value} is not a slot")
        return raw

    def value_of(self, raw: int) -> float:
        return float(raw)

    def raw_of_values(self, values: tuple[str, ...]) -> int | None:
        return raw_of_fields(values)

    def on_step(self, value: float) -> bool:
        return True


@dataclass(frozen=True)
class Program:
    """A program whose 21 slots the definitions prove writable on its device."""

    key: str  # <circuit>/<group id>, e.g. fs1/heating1
    circuit: str
    group: str
    device: str
    label: dict[str, str]
    slots: dict[int, tuple[str, str, str]]  # day 1..7 -> keys of its slots 1..3

    def day_keys(self, day: int) -> tuple[str, str, str]:
        return self.slots[day]


TEXT_FIELDS = ("totime", "toenabled", "fromtime", "fromenabled")


def program_specs(model: Model, loaded: dict[str, list[Definition]]) -> tuple[dict[str, Program],
                                                                              dict[str, SlotSpec], list[str]]:
    """The programs whose 21 slots all have write conditions in the metadata and a write definition ebusd loaded
    as the release has it, their slot specs, and the programs left out with the reason."""
    programs, specs, refused = {}, {}, []
    for group in model.groups.values():
        if group.family != "program":
            continue
        members = [model.messages[key] for key in group.members]
        if not all(m.write is not None for m in members):
            continue  # not proven on this device (room unit 2): never offered
        if any(m.write.risk != "comfort" for m in members):
            # a day is written at once, without a confirmation: a program of another class is not offered
            refused.append(f"{group.key}: risk class {sorted({m.write.risk for m in members})}, needs a confirmation")
            continue
        slots: dict[int, list[str]] = {}
        group_specs, reason = {}, ""
        for message in members:
            spec, reason = _slot_spec(message, loaded.get(message.circuit, []))
            if spec is None:
                break
            group_specs[message.key] = spec
            position = message.position or {}
            slots.setdefault(position["day"], [""] * SLOTS)[position["slot"] - 1] = message.key
        if reason or len(slots) != 7 or any("" in day for day in slots.values()):
            refused.append(f"{group.key}: {reason or 'incomplete'}")
            continue
        specs.update(group_specs)
        programs[group.key] = Program(group.key, group.circuit, group.id, group.device, group.label,
                                      {day: tuple(keys) for day, keys in sorted(slots.items())})
    return programs, specs, refused


def _slot_spec(message, definitions: list[Definition]) -> tuple[SlotSpec | None, str]:
    conditions = message.write
    if conditions.source not in ("ff", "31") or conditions.risk not in ("comfort", "regulation"):
        return None, f"{message.key}: write conditions"
    definition = next((d for d in definitions if d.name == message.name and d.direction == "w"), None)
    if definition is None:
        return None, f"{message.key}: ebusd did not load its write definition"
    loaded = [f for f in definition.fields if not f.type.startswith("IGN")]
    if (definition.pbsb.lower() != PBSB or definition.zz.lower() != message.address.lower()
            or len(definition.id) != 6 or WCRC_MARKER not in definition.comment
            or tuple(f.name for f in loaded) != TEXT_FIELDS
            or [f.type.split(":")[0] for f in loaded] != ["TTQ", "BI7", "TTQ", "BI7"]):
        return None, f"{message.key}: ebusd loaded another write definition"
    return SlotSpec(message.key, message.circuit, message.name, message.address.lower(), definition.id[2:].lower(),
                    "SLOT", 1, 0.0, 65535.0, 1.0, None, conditions.source, conditions.risk, conditions.proof,
                    tuple(conditions.open), "definitions"), ""
