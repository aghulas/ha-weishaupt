"""A simulated ebusd: a TCP server that answers `info`, `find -f -c` and `read` like ebusd does.

What it answers comes from tests/data/ebusd-golden.json, the text a real ebusd gave for the same commands (see
scripts/capture_ebusd.py): `info`, the definitions of every circuit, and the decoded values of the telegrams of
tests/data/telegrams.json. For a message without a recorded telegram it makes up a value of the right shape from
the definition (0, the first entry of a value list, 00:00).

It is a simulation: no bus, no timing of a bus, no arbitration. Every command received is kept in `commands`
with its time, so that a test can check what was asked, how often and how far apart.
"""
from __future__ import annotations

import asyncio
import csv
import io
import re
import time

_READ = re.compile(r"^read -m (\d+) -c (\S+) (\S+)$")
_FIND = re.compile(r"^find -f -c (\S+)$")


class FakeEbusd:
    def __init__(self, golden: dict) -> None:
        # the recording was made without a bus: a running installation reports a signal
        self.info = golden["info"].replace("signal: no signal", "signal: acquired")
        self.definitions: dict[str, str] = dict(golden["definitions"])
        self._golden_definitions: dict[str, str] = dict(golden["definitions"])
        self.reads: dict[str, str] = dict(golden["reads"])
        self.signal = True
        self.commands: list[tuple[float, str]] = []
        self.active = 0
        self.max_active = 0
        self.port = 0
        self._server: asyncio.Server | None = None

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
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            line = (await reader.readline()).decode().strip()
            if line:
                self.commands.append((time.monotonic(), line))
                writer.write(self.answer(line).encode() + b"\n\n")
                await writer.drain()
        finally:
            self.active -= 1
            writer.close()

    def answer(self, command: str) -> str:
        if command == "info":
            return self.info if self.signal else self.info.replace("signal: acquired", "signal: no signal")
        if match := _FIND.match(command):
            return self.definitions.get(match.group(1).lower()) or "ERR: element not found"
        if match := _READ.match(command):
            return self._read(match.group(2).lower(), match.group(3))
        return "ERR: command not found"

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
        return recorded or ";".join(_made_up(row[8:]))


def _made_up(cells: list[str]) -> list[str]:
    values = []
    for i in range(0, len(cells), 6):
        _name, _part, kind, divisor_or_values, _unit = (cells[i:i + 5] + [""] * 5)[:5]
        if kind.startswith("IGN"):
            continue
        if "=" in divisor_or_values:
            values.append(divisor_or_values.split(";")[0].split("=")[1])
        elif kind.startswith("TTQ"):
            values.append("00:00")
        elif kind.startswith("HEX"):
            values.append("00 00")
        elif kind in ("D2B", "D2C"):
            values.append("0.000")
        elif divisor_or_values.isdigit() and int(divisor_or_values) > 1:
            values.append("0.0")
        else:
            values.append("0")
    return values
