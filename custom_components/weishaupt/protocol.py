"""Weishaupt register access over ebusd, without Home Assistant dependencies.

Registers of the regulators (KA, EM, FS, SC) are read with 5022 and written with 5023, both protected by the
Weishaupt CRC (CRC-8, polynomial 0x5C, initial value = first byte) placed in the first data byte. The frames are sent
with the ebusd "hex" command (ebusd started with --enablehex); a write may override the source address with "-s".
Measured on the école Sainte-Marie bus (30/10/2026): a read answers 2 bytes per register, 0x8000 = not used; up to
4 registers per read; one register per write (a multi-register write is acknowledged too late for ebusd).
"""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass

MAX_READ_REGISTERS = 4
NOT_AVAILABLE = b"\x00\x80"


def crc_weishaupt(payload: bytes) -> int:
    """Weishaupt CRC over the ID and data bytes that follow it."""
    value = payload[0]
    for byte in payload[1:]:
        for _ in range(8):
            value = ((value << 1) ^ 0x5C) & 0xFF if value & 0x80 else (value << 1) & 0xFF
        value ^= byte
    return value


def read_command(zz: str, registers: list[str]) -> str:
    """ebusd hex command reading up to 4 registers ("RRBB", register and bank) of the device at slave address zz."""
    if not 1 <= len(registers) <= MAX_READ_REGISTERS:
        raise ValueError(f"1 to {MAX_READ_REGISTERS} registers per read, got {len(registers)}")
    payload = bytes.fromhex("".join(registers))
    return f"hex {zz}5022{len(payload) + 1:02x}{crc_weishaupt(payload):02x}{payload.hex()}"


def write_command(zz: str, register: str, raw: bytes, source: str | None = None) -> str:
    """ebusd hex command writing the 2 raw bytes of one register, from the source address if given."""
    if len(raw) != 2:
        raise ValueError("a register holds 2 bytes")
    payload = bytes.fromhex(register) + raw
    prefix = f"-s {source} " if source else ""
    return f"hex {prefix}{zz}5023{len(payload) + 1:02x}{crc_weishaupt(payload):02x}{payload.hex()}"


DATETIME_BROADCAST = "0700"  # standard eBUS date/time broadcast, which the clock master f1 takes over
_BROADCAST_OUTSIDE = re.compile(rf"f1fe{DATETIME_BROADCAST}[0-9a-f]{{2}}([0-9a-f]{{4}})", re.IGNORECASE)


def _bcd(value: int) -> str:
    """Two BCD digits of 0..99 as the ebusd hex byte (the decimal digits read straight as the byte, e.g. 30 -> 0x30)."""
    if not 0 <= value <= 99:
        raise ValueError(f"valeur BCD hors de 0..99 : {value}")
    return f"{value:02d}"


def datetime_broadcast_command(second: int, minute: int, hour: int, day: int, month: int, weekday: int, year: int,
                               outside_raw: bytes) -> str:
    """ebusd hex command broadcasting the standard date/time telegram (`fe 0700`), which sets the clock master f1.

    Time and date are BCD, weekday 1 = Monday .. 7 = Sunday, year its last two digits. `outside_raw` is the 2-byte
    outside-temperature field copied from f1's last broadcast (f1 overwrites it from its own sensor within a minute).
    Sent as a broadcast from ebusd's own address, without `-s ff`. Validated on the école Sainte-Marie bus
    (30/10/2026: `fe070009000d00591730100526` sent at 17:59:00 reset the whole installation to 30/10/2026 17:59)."""
    if len(outside_raw) != 2:
        raise ValueError("la température extérieure fait 2 octets")
    if not 1 <= weekday <= 7:
        raise ValueError("jour de semaine 1..7 (1 = lundi)")
    data = (outside_raw.hex() + _bcd(second) + _bcd(minute) + _bcd(hour)
            + _bcd(day) + _bcd(month) + _bcd(weekday) + _bcd(year))
    payload = bytes.fromhex(data)
    return f"hex fe{DATETIME_BROADCAST}{len(payload):02x}{data}"


def parse_last_outside_raw(grab_output: str) -> bytes | None:
    """Outside-temperature 2 bytes of f1's last date/time broadcast in `ebusctl grab result all` output (None if absent)."""
    matches = _BROADCAST_OUTSIDE.findall(grab_output)
    return bytes.fromhex(matches[-1]) if matches else None


def parse_read_answer(answer: str, registers: list[str]) -> dict[str, bytes | None]:
    """Split the answer of a read ("NN" + 2 bytes per register) into raw values; None = register not used."""
    data = bytes.fromhex(answer)
    if not data or data[0] != 2 * len(registers) or len(data) != 1 + data[0]:
        raise EbusdError(f"unexpected answer {answer!r} for {registers}")
    values = {}
    for i, register in enumerate(registers):
        raw = data[1 + 2 * i:3 + 2 * i]
        values[register] = None if raw == NOT_AVAILABLE else raw
    return values


@dataclass(frozen=True)
class Codec:
    """Signed 16-bit little-endian value divided by a factor (Weishaupt _16_Temp10, _16_Percent, ...)."""

    factor: int = 1
    signed: bool = True

    def decode(self, raw: bytes) -> float:
        return int.from_bytes(raw, "little", signed=self.signed) / self.factor

    def encode(self, value: float) -> bytes:
        return int(round(value * self.factor)).to_bytes(2, "little", signed=self.signed)


TEMP10 = Codec(10)  # °C or K with one decimal
UNIT = Codec(1, signed=False)  # percent, day, month, year (low byte)


UNUSED_SLOT = b"\x80\x80"


def decode_slot(raw: bytes) -> tuple[int, int] | None:
    """Time program slot: byte 0 = end, byte 1 = start, in quarters of an hour; 0x80 0x80 = unused.

    Returns (start, end) in minutes since midnight."""
    if raw == UNUSED_SLOT:
        return None
    return raw[1] * 15, raw[0] * 15


def encode_slot(slot: tuple[int, int] | None) -> bytes:
    if slot is None:
        return UNUSED_SLOT
    start, end = slot
    if not (0 <= start < end <= 24 * 60 and start % 15 == 0 and end % 15 == 0):
        raise ValueError(f"invalid slot {slot}: quarters of an hour, start before end")
    return bytes([end // 15, start // 15])


def format_slots(slots: list[tuple[int, int] | None]) -> str:
    used = [s for s in slots if s]
    return ", ".join(f"{a // 60:02d}:{a % 60:02d}-{b // 60:02d}:{b % 60:02d}" for a, b in used) or "-"


def parse_slots(text: str) -> list[tuple[int, int]]:
    """'06:30-18:00, 19:00-21:00' -> [(390, 1080), (1140, 1260)]; '' or '-' = no slot; up to 3, ascending."""
    slots = []
    for part in text.replace(";", ",").split(","):
        part = part.strip()
        if not part or part == "-":
            continue
        a, b = (x.strip() for x in part.split("-"))
        to_min = lambda t: int(t.split(":")[0]) * 60 + int(t.split(":")[1])  # noqa: E731
        slots.append((to_min(a), to_min(b)))
    if len(slots) > 3:
        raise ValueError("3 slots per day at most")
    for i, slot in enumerate(slots):
        encode_slot(slot)
        if i and slot[0] < slots[i - 1][1]:
            raise ValueError("slots must be ascending and not overlap")
    return slots


class EbusdError(Exception):
    """ebusd refused the command or the device did not answer as expected."""


class EbusdClient:
    """Minimal ebusd TCP client: one command at a time, one connection per command."""

    def __init__(self, host: str, port: int, timeout: float = 10.0) -> None:
        self.host, self.port, self.timeout = host, port, timeout
        self._lock = asyncio.Lock()

    async def command(self, text: str) -> str:
        async with self._lock:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(self.host, self.port), self.timeout)
            try:
                writer.write(text.encode() + b"\n")
                await writer.drain()
                buf = b""
                while b"\n\n" not in buf:
                    chunk = await asyncio.wait_for(reader.read(4096), self.timeout)
                    if not chunk:
                        break
                    buf += chunk
            finally:
                writer.close()
                await writer.wait_closed()
        answer = buf.split(b"\n\n", 1)[0].decode().strip()
        if answer.startswith("ERR"):
            raise EbusdError(f"{text}: {answer}")
        return answer

    async def read_registers(self, zz: str, registers: list[str]) -> dict[str, bytes | None]:
        values: dict[str, bytes | None] = {}
        for i in range(0, len(registers), MAX_READ_REGISTERS):
            chunk = registers[i:i + MAX_READ_REGISTERS]
            values.update(parse_read_answer(await self.command(read_command(zz, chunk)), chunk))
        return values

    async def write_register(self, zz: str, register: str, raw: bytes, source: str | None = None) -> None:
        """ÉCRITURE: one register with 5023; the caller reads it back (an acknowledge does not prove the value)."""
        answer = await self.command(write_command(zz, register, raw, source))
        if answer != "00":
            raise EbusdError(f"write {zz} {register}: answer {answer!r}")

    async def last_outside_raw(self) -> bytes | None:
        """Outside-temperature bytes of f1's last date/time broadcast, from ebusd's grab buffer (None if not captured)."""
        try:
            return parse_last_outside_raw(await self.command("grab result all"))
        except EbusdError:
            return None

    async def broadcast_datetime(self, command: str) -> None:
        """ÉCRITURE (diffusion): send a prebuilt `fe 0700` telegram; ebusd answers "done broadcast"."""
        answer = await self.command(command)
        if "done" not in answer:
            raise EbusdError(f"broadcast {command}: answer {answer!r}")
