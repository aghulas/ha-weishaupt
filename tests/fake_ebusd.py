"""A simulated ebusd: a TCP server that answers `info`, `find -f [-w] -c`, `read` and `write -h` like ebusd does.

What it answers comes from tests/data/ebusd-golden.json, the text a real ebusd gave for the same commands (see
scripts/capture_ebusd.py): `info`, the definitions of every circuit, and for every message of the definitions the
values of one telegram captured on a bus (the fixtures file of the definitions release). No value is made up: a
message without a recording answers an error.

Writes (`write [-s QQ] -c <circuit> -h <bytes>`) follow what ebusd does (src/ebusd/mainloop.cpp, executeWrite, and
the run-time checksum of john30/ebusd#1825 in src/lib/ebus/message.cpp): the bytes are matched against the loaded
write definitions (`write_definitions` of the recording), with the run-time checksum when `runtime_checksum` is
true (the fork's build) or byte for byte otherwise (a stock ebusd); no match answers `ERR: element not found`, a
match of another circuit `ERR: invalid argument`, and a match is "sent": kept in `writes`, acknowledged `00`, and
the register takes the value, so that a read (`read -f` included) answers it, unless the test said the device does
not take it over (`not_taken`). The recording holds the answers of both builds to the same commands; a test checks
that this simulation gives each of them.

It is a simulation: no bus, no timing of a bus, no arbitration. Every command received is kept in `commands`
with its time, so that a test can check what was asked, how often and how far apart.
"""
from __future__ import annotations

import asyncio
import csv
import io
import re
import time
from datetime import datetime

_READ_AGE = re.compile(r"^read -m (\d+) -c (\S+) (\S+)$")
_READ = re.compile(r"^read (?:-m \d+|-f) -c (\S+) (\S+)$")
_FIND = re.compile(r"^find -f (-w )?-c (\S+)$")
_WRITE = re.compile(r"^write (?:-s ([0-9a-f]{2}) )?-c (\S+) -h ([0-9a-f]+)$")


def crc(data: bytes) -> int:
    value = data[0]
    for byte in data[1:]:
        for _ in range(8):
            value = ((value << 1) ^ 0x5C) & 0xFF if value & 0x80 else (value << 1) & 0xFF
        value ^= byte
    return value


def _neutral(type_: str, divisor_or_values: str) -> str:
    """A plausible decoded value for a field without a recorded answer."""
    if "=" in divisor_or_values:
        return divisor_or_values.split(";")[0].split("=", 1)[1]
    if type_.startswith(("TTQ", "TTH", "TTM")):
        return "00:00"
    if type_.startswith(("HEX", "STR", "NTS")):
        return "-"
    if divisor_or_values and divisor_or_values.lstrip("-").isdigit() and int(divisor_or_values) > 1:
        return f"{0:.{len(divisor_or_values) - 1}f}"
    return "0"


class FakeEbusd:
    def __init__(self, golden: dict) -> None:
        # the recording was made without a bus: a running installation reports a signal
        self.info = golden["info"].replace("signal: no signal", "signal: acquired")
        self.definitions: dict[str, str] = dict(golden["definitions"])
        self._golden_definitions: dict[str, str] = dict(golden["definitions"])
        self.reads: dict[str, str] = dict(golden["reads"])
        # a message the release has no fixture for (definitions 0.6.0: 51, mostly of room units 2 and 3) gets an
        # answer: the recorded one of the same message on another circuit, else a neutral value per field
        self.synthesized: set[str] = set()
        self._synthesize()
        self.write_definitions: dict[str, str] = dict(golden["write_definitions"])
        self.runtime_checksum = True  # the fork's build; False: a stock ebusd
        self.not_taken: set[str] = set()  # settings whose device acknowledges a write and keeps its value
        self.writes: list[tuple[str | None, str, str]] = []  # (source, circuit, bytes) of every write "sent"
        self.signal = True
        # Optional timing, for the bench of the first pass: ebusd's cache (a value it read less than `-m` seconds
        # ago is answered at once, without a telegram) and the time of an answer from the cache and from the bus.
        # Off by default: the other tests answer at once and do not model the cache.
        self.model_cache = False
        self.cache: dict[str, float] = {}  # key -> time ebusd last read it from the bus
        self.latency_cache = 0.0
        self.latency_bus = 0.0
        self.bus: list[tuple[float, str]] = []  # telegrams a read put on the bus (with model_cache)
        # the last date and time broadcast ebusd holds (passive Datetime of the general broadcast file): the bytes
        # recorded from a real ebusd, received now unless a test says otherwise
        self.clock_raw: str | None = golden["clock"]["telegram"].rstrip("/")
        self.clock_received: datetime | None = None
        self.commands: list[tuple[float, str]] = []
        self.active = 0
        self.max_active = 0
        self.port = 0
        self._server: asyncio.Server | None = None
        self._prev_handler = None

    def _synthesize(self) -> None:
        by_name: dict[str, str] = {}
        for key, text in self.reads.items():
            by_name.setdefault(key.split("/")[1], text)
        for circuit, text in self.definitions.items():
            for row in csv.reader(io.StringIO(text)):
                if len(row) < 8 or not row[0].startswith("r") or f"{circuit}/{row[2]}" in self.reads:
                    continue
                key = f"{circuit}/{row[2]}"
                fields = [row[i:i + 6] for i in range(8, len(row) - 5, 6)]
                fields = [f for f in fields if f and f[0] and not f[2].startswith("IGN")]
                if row[2] in by_name and len(by_name[row[2]].split(";")) == len(fields):
                    answer = by_name[row[2]]
                else:
                    answer = ";".join(_neutral(f[2], f[3]) for f in fields)
                self.reads[key] = answer
                self.synthesized.add(key)

    # ---- knobs for the tests --------------------------------------------------------------------------------

    def remove_message(self, key: str) -> None:
        circuit, name = key.split("/")
        self.definitions[circuit] = "\n".join(
            line for line in self.definitions[circuit].splitlines() if line.split(",")[2] != name)

    def edit_message(self, key: str, old: str, new: str) -> None:
        circuit, name = key.split("/")
        lines = self.definitions[circuit].splitlines()
        self.definitions[circuit] = "\n".join(
            line.replace(old, new) if line.split(",")[2] == name else line for line in lines)

    def remove_address(self, address: str) -> None:
        self.info = "\n".join(line for line in self.info.splitlines() if not line.startswith(f"address {address}:"))

    def reads_of(self, verb: str = "read") -> list[tuple[float, str]]:
        return [(when, text) for when, text in self.commands if text.split()[0] == verb]

    # ---- server ---------------------------------------------------------------------------------------------

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        self._prev_handler = loop.get_exception_handler()
        loop.set_exception_handler(self._drop_accept_race)
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            try:
                await self._server.wait_closed()
            except (RuntimeError, AttributeError):  # asyncio server internals racing with the close
                pass
            self._server = None
        loop = asyncio.get_running_loop()
        if loop.get_exception_handler() is self._drop_accept_race:
            loop.set_exception_handler(self._prev_handler)

    def _drop_accept_race(self, loop: asyncio.AbstractEventLoop, context: dict) -> None:
        """A client (the hub's reconnect loop under `fast_retry`) can land on the listening socket just as a test
        closes it; asyncio then reports a benign accept error. Drop that one message, pass everything else on (to
        Home Assistant's own catcher, which fails the test on a real error)."""
        if "transport creation for incoming connection" in context.get("message", ""):
            return
        if self._prev_handler is not None:
            self._prev_handler(loop, context)
        else:
            loop.default_exception_handler(context)

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            line = (await reader.readline()).decode().strip()
            if line:
                self.commands.append((time.monotonic(), line))
                delay = self._delay(line)
                if delay:
                    await asyncio.sleep(delay)
                writer.write(self.answer(line).encode() + b"\n\n")
                await writer.drain()
        finally:
            self.active -= 1
            writer.close()

    def _delay(self, command: str) -> float:
        """With `model_cache`: a read answered from ebusd's cache, or one that goes to the bus (kept in `bus`)."""
        if not self.model_cache or not (match := _READ_AGE.match(command)):
            return 0.0
        age, key = int(match.group(1)), f"{match.group(2).lower()}/{match.group(3)}"
        row = self._definition(match.group(2).lower(), match.group(3))
        if row is None or row[0].startswith("u"):
            return self.latency_cache
        now = time.monotonic()
        if age and now - self.cache.get(key, -1e9) < age:
            return self.latency_cache
        self.cache[key] = now
        self.bus.append((now, key))
        return self.latency_bus

    def answer(self, command: str) -> str:
        if command == "info":
            return self.info if self.signal else self.info.replace("signal: acquired", "signal: no signal")
        if command == "find -p -h -vvv -c broadcast Datetime":
            if self.clock_raw is None:
                return "Broadcast Datetime = no data stored [ZZ=fe, passive read]"
            received = self.clock_received or datetime.now()
            return (f"Broadcast Datetime = {self.clock_raw} /  [ZZ=fe, lastup={received:%Y-%m-%d %H:%M:%S}, "
                    "passive read]")
        if match := _FIND.match(command):
            table = self.write_definitions if match.group(1) else self.definitions
            return table.get(match.group(2).lower()) or "ERR: element not found"
        if match := _READ.match(command):
            return self._read(match.group(1).lower(), match.group(2))
        if match := _WRITE.match(command):
            return self._write(match.group(1), match.group(2), match.group(3))
        if command.startswith(("write", "hex")):
            return "ERR: invalid argument" if command.startswith("write") else "ERR: command not enabled"
        return "ERR: command not found"

    def _write_definition(self, master: bytes) -> list[str] | None:
        """The write definition the bytes `ZZ PB SB NN data` match, as ebusd finds it."""
        zz, pbsb, data = master[:1].hex(), master[1:3].hex(), master[4:]
        for circuit_text in self.write_definitions.values():
            for row in csv.reader(io.StringIO(circuit_text)):
                if len(row) < 9 or row[0] != "w" or row[5] != zz or row[6] != pbsb:
                    continue
                ident = bytes.fromhex(row[7])
                dynamic = self.runtime_checksum and "[WCRC]" in row[3]
                if dynamic:
                    if data[1:len(ident)] == ident[1:] and data[0] == crc(data[1:]):
                        return row
                elif data[:len(ident)] == ident:
                    return row
        return None

    def _write(self, source: str | None, circuit: str, text: str) -> str:
        master = bytes.fromhex(text)
        row = self._write_definition(master)
        if row is None:
            return "ERR: element not found"
        if row[1] != circuit:
            return "ERR: invalid argument"
        if not self.signal:
            return "ERR: no signal"
        self.writes.append((source, circuit, text))
        if master[0] == 0xFE:  # a broadcast: no answer, and ebusd now holds it as the last one
            self.clock_raw, self.clock_received = f"31{text}", datetime.now()
            return "done broadcast"
        key = f"{row[1]}/{row[2]}"
        if key not in self.not_taken and row[10] == "TTQ":  # a program slot: end, its flag, start, its flag
            def part(byte: int) -> str:
                quarter = byte & 0x7F
                return f"{quarter // 4:02d}:{quarter % 4 * 15:02d};{'Disabled' if byte & 0x80 else 'Enabled'}"
            self.reads[key] = f"{part(master[-2])};{part(master[-1])}"
        elif key not in self.not_taken:
            raw = int.from_bytes(master[-2:], "little", signed=row[10] == "SIN")
            if "=" in row[11]:  # a value list: ebusd answers the name of the entry
                names = dict(item.split("=", 1) for item in row[11].split(";"))
                self.reads[key] = names.get(str(raw), str(raw))
            else:
                divisor = int(row[11]) if row[11] else 1
                self.reads[key] = f"{raw / divisor:.1f}" if divisor > 1 else str(raw)
        return "00"

    def _definition(self, circuit: str, name: str) -> list[str] | None:
        for row in csv.reader(io.StringIO(self.definitions.get(circuit, ""))):
            if len(row) > 8 and row[2] == name and row[0][0] in "ru":
                return row
        return None

    def _read(self, circuit: str, name: str) -> str:
        row = self._definition(circuit, name)
        if row is None:
            return "ERR: element not found"
        passive = row[0].startswith("u")
        recorded = self.reads.get(f"{circuit}/{name}")
        if passive:
            return recorded or "ERR: no data stored"
        if not self.signal:
            return "ERR: no signal"
        return recorded or "ERR: no recorded answer for this message"

