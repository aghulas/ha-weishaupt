"""The fault memory of the boilers, their fault counters and the fault log of the system manager, from the readings
of their messages. No Home Assistant dependency: the fault-history sensor and the panel build on it.

Boiler fault history: six slots of 8 bytes; the pointer is the address of the last byte written, slot n ends at
0x0201 + 8 n (evidence record `bc-fault-history` of the definitions). The automat stores no time with an entry.
Fault counters: one field `code<n>` per fault number, whose description in the definitions is the text of the
manual's fault list ("W57/F57: …"); that text names the faults of the history too.
System manager: the fault log entry its operating unit has selected (`em1/Error*`), with its time. Selecting
another entry is a write: the panel shows the selected one only."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .model import Group, Message, Model

FAULT_SLOT_BASE, FAULT_SLOT_SIZE = 0x0201, 8
NOT_AVAILABLE = "-"
LOG_FIELDS = ("Id", "Code", "Type", "Device", "Minute", "Hour", "Day", "Month", "Year")

Reading = Callable[[str], tuple[str, ...] | None]  # key -> values of its last reading, None when unread


def number(text: str | None) -> int | float | None:
    if text is None or text == NOT_AVAILABLE:
        return None
    try:
        return float(text) if "." in text else int(text)
    except ValueError:
        return None


def _fields(model: Model, reading: Reading, key: str) -> dict[str, str] | None:
    values = reading(key)
    if values is None:
        return None
    return {fld.name: values[fld.index] for fld in model.messages[key].fields if fld.index < len(values)}


def history(model: Model, reading: Reading, group: Group, pointer: str | None) -> list[dict[str, Any]] | None:
    """The entries of a fault memory, most recent first when the pointer was read; None while a slot is unread.
    Each entry: slot, code (`F11`, `W12`), and the values the automat stored with it."""
    slots = []
    for key in group.members:
        fields = _fields(model, reading, key)
        if fields is None:
            return None
        message = model.messages[key]
        value = number(fields.get("number"))
        entry: dict[str, Any] = {"slot": (message.position or {}).get("n")}
        if value:  # an empty slot reads 0
            entry["code"] = f"{'W' if fields.get('kind') == 'warning' else 'F'}{value}"
            entry["number"] = value
            for fld in message.fields:
                if fld.shown and fld.name not in ("number", "kind"):
                    text = fields[fld.name]
                    entry[fld.name] = text if fld.values else number(text)
        slots.append(entry)
    newest = None
    if pointer and (found := _fields(model, reading, pointer)) is not None:
        position = number(found.get("value"))
        if isinstance(position, int) and (position - FAULT_SLOT_BASE) % FAULT_SLOT_SIZE == 0:
            newest = (position - FAULT_SLOT_BASE) // FAULT_SLOT_SIZE
    if newest is not None and 1 <= newest <= len(slots):
        slots = [slots[(newest - 1 - i) % len(slots)] for i in range(len(slots))]
    return [entry for entry in slots if "code" in entry]


def counter_fields(model: Model, circuit: str) -> list[tuple[Message, int, int]]:
    """(message, index of the field, fault number) of each fault counter of a circuit, in the order of the
    definitions."""
    out = []
    for group in model.groups.values():
        if group.family != "fault_counter" or group.circuit != circuit:
            continue
        for key in group.members:
            message = model.messages[key]
            for fld in message.fields:
                if fld.shown and fld.name.startswith("code") and fld.name[4:].isdigit():
                    out.append((message, fld.index, int(fld.name[4:])))
    return out


def texts(model: Model, circuit: str) -> dict[int, dict[str, str]]:
    """Fault number -> the text of the manual's list, from the descriptions of the counters (empty when the
    definitions carry none)."""
    found = {}
    for message, index, value in counter_fields(model, circuit):
        description = message.fields[index].description
        if description:
            found[value] = description
    return found


def counters(model: Model, reading: Reading, circuit: str) -> list[dict[str, Any]]:
    """Each fault counter: number, count (None while unread), text."""
    known = texts(model, circuit)
    out = []
    for message, index, value in counter_fields(model, circuit):
        values = reading(message.key)
        count = number(values[index]) if values is not None and index < len(values) else None
        out.append({"number": value, "count": count, "text": known.get(value), "key": message.key})
    return out


def log_keys(model: Model, circuit: str) -> list[str]:
    return [key for name in LOG_FIELDS if (key := f"{circuit}/Error{name}") in model.messages]


def log_entry(model: Model, reading: Reading, circuit: str) -> dict[str, Any] | None:
    """The fault-log entry selected on the system manager: id, code, type, origin, time; None while unread or
    when the definitions have no fault log."""
    keys = log_keys(model, circuit)
    if not keys:
        return None
    values: dict[str, int | float | None] = {}
    for key in keys:
        found = reading(key)
        if found is None:
            return None
        values[key.split("/Error", 1)[1].lower()] = number(found[0]) if found else None
    day, month, year = values.get("day"), values.get("month"), values.get("year")
    hour, minute = values.get("hour"), values.get("minute")
    when = None
    if None not in (day, month, year, hour, minute):
        when = f"{int(year):04d}-{int(month):02d}-{int(day):02d} {int(hour):02d}:{int(minute):02d}"  # type: ignore[arg-type]
    return {"id": values.get("id"), "code": values.get("code"), "type": values.get("type"),
            "device": values.get("device"), "time": when}
