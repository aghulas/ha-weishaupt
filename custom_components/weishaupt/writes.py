"""What may be written, and the bytes of a write. No Home Assistant dependency.

A setting is writable only when the metadata of the definitions release gives it write conditions (a lot proves
the write, an evidence record names it) and ebusd loaded its write definition as the release has it. Structural
settings never have write conditions; anything else in the metadata stays read-only.

The telegram of a write is built here, byte for byte, and sent with `write -c <circuit> -h <bytes>`: ebusd sends it
only when the bytes match the write definition it loaded for that circuit, the run-time checksum included on a
build that has it (john30/ebusd#1825). A register write is `ZZ 50 23 05 <crc> <addr> <sub> <low> <high>`: one 16-bit
register per telegram, value low byte first, `<crc>` a CRC-8 (polynomial 0x5C) over the four bytes after it
(`evidence/register-write-crc.md` of the definitions).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .ebusd import Definition
from .model import Message, Model

PBSB = "5023"
WCRC_MARKER = "[WCRC]"

# Ranges the metadata does not carry (`open.range` of the metadata: the definitions have none, the bounds are
# fractional), quoted from the evidence record `settings-writes.md` of the definitions, which takes them from the
# vendor's installation manual of the room unit and heating circuit (WCM-FS 2.0) and states them for heating module
# 2; the record gives the other heating circuits and room units "as on em2". Step 0.5 as every other temperature
# of the lot and the changes proven on the bus. A contract gap: to be carried by the metadata.
FALLBACK_RANGES: dict[str, tuple[float, float, float]] = {
    "RoomSetbackTemp": (10.0, 21.5, 0.5),
    "GradientCurve": (2.5, 40.0, 0.5),
}
# Linked bounds, which no record of the definitions states: on one circuit the setback room temperature stays at
# or below the normal one, the minimum flow temperature at or below the maximum. (lower, upper) message names.
LINKED: tuple[tuple[str, str], ...] = (
    ("RoomSetbackTemp", "RoomNormalTemp"),
    ("SupplyMinTemp", "SupplyMaxTemp"),
)
TYPES = {"UIN": (0, 0xFFFE), "SIN": (-0x7FFF, 0x7FFF)}  # 0xffff and 0x8000 are the replacement values
RISKS = ("comfort", "regulation")  # structural settings are never in the metadata's write conditions


def crc(data: bytes) -> int:
    """CRC-8, polynomial 0x5C, initial value the first byte, over all the bytes given."""
    value = data[0]
    for byte in data[1:]:
        for _ in range(8):
            value = ((value << 1) ^ 0x5C) & 0xFF if value & 0x80 else (value << 1) & 0xFF
        value ^= byte
    return value


def round_half_away(value: float) -> int:
    """How ebusd turns a value times its divisor into an integer."""
    return int(math.floor(abs(value) + 0.5)) * (1 if value >= 0 else -1)


@dataclass(frozen=True)
class WriteSpec:
    """A writable setting, as the metadata describes it and ebusd loaded it."""

    key: str  # <circuit>/<name>
    circuit: str
    name: str
    zz: str  # target address
    register: str  # address and sub-address, 4 hex digits ("2500")
    type: str  # "UIN" or "SIN"
    divisor: int
    minimum: float
    maximum: float
    step: float
    unit: str | None
    source: str  # "ff" or "31"
    risk: str  # "comfort" or "regulation"
    proof: str
    open: tuple[str, ...]
    bounds_from: str  # "definitions", or "evidence" for the fallback ranges

    @property
    def ebusd_source(self) -> str | None:
        """The `-s` of the write command: "ff" for a setting proven from the address of the vendor service tool,
        None (ebusd's own address) for one proven from 31. Taken from the metadata, never decided here."""
        return "ff" if self.source == "ff" else None

    @property
    def register_id(self) -> str:
        """Key of the rate limit: the device register, whatever circuit name it is reached through."""
        return f"{self.zz}:{self.register}"

    def raw(self, value: float) -> int:
        """Register value for `value` (the value times the divisor, rounded as ebusd does)."""
        raw = round_half_away(value * self.divisor)
        low, high = TYPES[self.type]
        if not low <= raw <= high:
            raise ValueError(f"{value} does not fit the type {self.type}")
        return raw

    def value_of(self, raw: int) -> float:
        return raw / self.divisor if self.divisor > 1 else float(raw)

    def raw_of_text(self, text: str) -> int | None:
        """Register value of what ebusd answers to a read of the setting, None when it is no number."""
        try:
            return round_half_away(float(text) * self.divisor)
        except ValueError:
            return None

    def on_step(self, value: float) -> bool:
        steps = (value - self.minimum) / self.step
        return abs(steps - round(steps)) < 1e-6

    def telegram(self, value: float) -> str:
        """Target, command, length and data in hex, as `write -h` takes them: `15502305282500` + `0100`."""
        raw = self.raw(value) & 0xFFFF
        body = bytes.fromhex(self.register) + raw.to_bytes(2, "little")
        return f"{self.zz}{PBSB}05{crc(body):02x}{body.hex()}"

    def placeholder_telegram(self, value: float, placeholder: str) -> str:
        """The same telegram with the checksum byte of the definition (the checksum of the address alone)."""
        telegram = self.telegram(value)
        return telegram[:8] + placeholder + telegram[10:]


@dataclass(frozen=True)
class NotWritable:
    key: str
    reason: str


def write_specs(model: Model, loaded: dict[str, list[Definition]]) -> tuple[dict[str, WriteSpec],
                                                                             list[NotWritable], dict[str, str]]:
    """Specs of the settings the metadata marks writable and ebusd loaded as expected (`loaded`: circuit -> the
    write definitions of `find -f -w`), the settings left read-only with the reason, and the checksum byte of
    each definition (the placeholder ebusd replaces when it has the run-time checksum)."""
    specs, refused, placeholders = {}, [], {}
    for message in model.messages.values():
        if message.write is None:
            continue
        spec, reason, placeholder = _spec(message, loaded.get(message.circuit, []))
        if spec is None:
            refused.append(NotWritable(message.key, reason))
        else:
            specs[message.key] = spec
            placeholders[message.key] = placeholder
    return specs, refused, placeholders


def _spec(message: Message, definitions: list[Definition]) -> tuple[WriteSpec | None, str, str]:
    conditions = message.write
    assert conditions is not None
    if conditions.risk not in RISKS:
        return None, f"risk class {conditions.risk!r}", ""
    if conditions.source not in ("ff", "31"):
        return None, f"source {conditions.source!r}", ""
    fields = [f for f in message.fields if f.shown]
    if len(fields) != 1 or fields[0].type not in TYPES:
        return None, "not one 16-bit number", ""
    fld = fields[0]
    definition = next((d for d in definitions if d.name == message.name and d.direction == "w"), None)
    if definition is None:
        return None, "ebusd did not load its write definition", ""
    loaded_fields = [f for f in definition.fields if not f.type.startswith("IGN")]
    divisor = fld.divisor or 1
    if (definition.pbsb.lower() != PBSB or definition.zz.lower() != message.address.lower()
            or len(definition.id) != 6 or WCRC_MARKER not in definition.comment
            or len(loaded_fields) != 1 or loaded_fields[0].type != fld.type
            or loaded_fields[0].divisor_or_values != ("" if divisor == 1 else str(divisor))):
        return None, "ebusd loaded another write definition", ""
    minimum, maximum, step, bounds_from = fld.minimum, fld.maximum, fld.step, "definitions"
    if minimum is None or maximum is None:
        if message.name not in FALLBACK_RANGES:
            return None, "no range", ""
        minimum, maximum, step = FALLBACK_RANGES[message.name]
        bounds_from = "evidence"
    if step is None:
        step = 1.0 if divisor == 1 else 1.0 / divisor
    spec = WriteSpec(message.key, message.circuit, message.name, message.address.lower(), definition.id[2:].lower(),
                     fld.type, divisor, float(minimum), float(maximum), float(step), fld.unit, conditions.source,
                     conditions.risk, conditions.proof, tuple(conditions.open), bounds_from)
    return spec, "", definition.id[:2].lower()


def linked(spec: WriteSpec, specs: dict[str, WriteSpec]) -> tuple[WriteSpec | None, WriteSpec | None]:
    """(setting this one must stay at or above, setting it must stay at or below), on the same circuit."""
    below = above = None
    for lower, upper in LINKED:
        if spec.name == upper:
            below = specs.get(f"{spec.circuit}/{lower}")
        if spec.name == lower:
            above = specs.get(f"{spec.circuit}/{upper}")
    return below, above


def capability(matched_correct: str, matched_placeholder: str) -> str:
    """Whether ebusd computes the run-time checksum, from its answers to two probes of one write telegram that
    differ only in the checksum byte (`EbusdClient.probe_write`): the correct checksum and the placeholder of the
    definition. Neither probe is sent to the bus.

    - "present": the correct checksum matched, the placeholder did not (the fork's build);
    - "absent": the placeholder matched, the correct one did not (a stock ebusd compares the byte as written);
    - "unknown": anything else."""
    if matched_correct == "matched" and matched_placeholder == "not found":
        return "present"
    if matched_correct == "not found" and matched_placeholder == "matched":
        return "absent"
    return "unknown"
