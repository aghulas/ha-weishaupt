"""Client of the ebusd TCP command port, without Home Assistant dependencies.

Generic: nothing here knows a manufacturer. It sends the three commands that read (`info`, `find`, `read`), and
one narrow form of `write`: a register write given as bytes and checked by ebusd against a write definition it
loaded (`write [-s QQ] -c <circuit> -h <ZZ PB SB NN data>`, see `REGISTER_WRITE`). Every other command is refused
before anything is sent: no `hex`, no `write` by name, no `-def`, no other length or command bytes. One connection
per command, one command at a time.

Formats as answered by ebusd 26.1 (recorded in tests/data/ebusd-golden.json):

- `info`: `version: ebusd 26.1…`, `signal: acquired`, then one line per address, for example
  `address 08: slave #11, scanned "MF=Kromschroeder;ID=W;SW=1104;HW=0102", loaded "kromschroeder/08.w.bc1.csv"`;
- `find -f -c <circuit>`: the definitions as CSV, `type,circuit,name,comment,qq,zz,pbsb,id` followed by six columns
  per field (`name,part,type,divisor/values,unit,comment`);
- `read -m <age> -c <circuit> <name>`: the values of all fields but the ignored ones, separated by `;`;
- `write -c <circuit> -h <bytes>`: ebusd looks for a loaded write definition whose bytes match (with the run-time
  checksum of the fork, john30/ebusd#1825: the checksum byte too), refuses the command when none matches
  (`ERR: element not found`) or when it belongs to another circuit (`ERR: invalid argument`), and otherwise sends
  the telegram and answers the bytes of the acknowledgement (`00`);
- an error is a line starting with `ERR: `.
"""
from __future__ import annotations

import asyncio
import csv
import io
import re
from dataclasses import dataclass, field

DEFAULT_PORT = 8888
PROBE_CIRCUIT = "weishaupt-probe"  # a circuit name no definition uses
READ_VERBS = frozenset({"info", "find", "read"})
# Options of `read` that send something else than the read of a loaded definition: a raw telegram (-h), a
# definition given on the command line (-def), another source or destination address (-s, -d), input data (-i).
FORBIDDEN_READ_OPTIONS = frozenset({"-h", "-def", "-s", "-d", "-i"})
# The only write: one 16-bit register (command 50 23, five data bytes: checksum, address, sub-address, value low,
# value high), from the address of the vendor service tool (ff) or ebusd's own, matched by ebusd to a write
# definition of the named circuit.
REGISTER_WRITE = re.compile(r"^write (?:-s ff )?-c [a-z0-9_-]+ -h [0-9a-f]{2}502305[0-9a-f]{10}$")


class EbusdError(Exception):
    """ebusd answered an error, or the command could not be sent."""


class EbusdConnectionError(EbusdError):
    """ebusd cannot be reached, or did not answer in time."""


class EbusdNoSignal(EbusdError):
    """ebusd has no signal on the bus (adapter unplugged, bus down)."""


class EbusdNoData(EbusdError):
    """No value stored for a passive message: its telegram has not been seen yet."""


class EbusdNotFound(EbusdError):
    """ebusd has no message of that circuit and name."""


class EbusdInvalidArgument(EbusdError):
    """ebusd refused the arguments (for `write -h`: a definition matched, of another circuit)."""


class CommandRefused(EbusdError):
    """The command is not one the client may send: it was not sent."""


def check_command(command: str) -> None:
    """Raise CommandRefused unless the command reads through loaded definitions or is the one register write."""
    if command.startswith("write ") and REGISTER_WRITE.match(command):
        return
    check_read_only(command)


def check_read_only(command: str) -> None:
    """Raise CommandRefused unless the command only reads through loaded definitions."""
    tokens = command.split()
    if not tokens or tokens[0] not in READ_VERBS:
        raise CommandRefused(f"refused, not a reading command: {command!r}")
    if tokens[0] == "read" and FORBIDDEN_READ_OPTIONS.intersection(tokens[1:]):
        raise CommandRefused(f"refused, raw or redirected read: {command!r}")


@dataclass(frozen=True)
class BusAddress:
    """One `address` line of `info`."""

    address: str
    role: str  # "master" or "slave"
    own: bool = False  # ebusd itself
    manufacturer: str | None = None
    ident: str | None = None
    software: str | None = None
    hardware: str | None = None
    files: tuple[str, ...] = ()

    @property
    def scanned(self) -> bool:
        return self.manufacturer is not None or self.ident is not None


@dataclass(frozen=True)
class EbusdInfo:
    version: str
    signal: bool
    addresses: dict[str, BusAddress] = field(default_factory=dict)
    values: dict[str, str] = field(default_factory=dict)  # the other "key: value" lines

    def slave(self, address: str) -> BusAddress | None:
        found = self.addresses.get(address.lower())
        return found if found is not None and found.role == "slave" and not found.own else None


_ADDRESS = re.compile(r"^address ([0-9a-f]{2}): (master|slave)([^\"]*)(.*)$")
_SCANNED = re.compile(r'scanned "([^"]*)"')
_LOADED = re.compile(r'loaded ((?:"[^"]*"(?:, )?)+)')


def parse_info(text: str) -> EbusdInfo:
    version, signal, addresses, values = "", False, {}, {}
    for line in text.splitlines():
        match = _ADDRESS.match(line.strip())
        if match is None:
            key, _, value = line.partition(":")
            if value:
                values[key.strip()] = value.strip()
            continue
        address, role, plain, quoted = match.groups()
        scanned, files_match = _SCANNED.search(line), _LOADED.search(line)
        parts = scanned.group(1).split(";") if scanned else []
        ident = dict(part.split("=", 1) for part in parts if "=" in part)
        files = tuple(re.findall(r'"([^"]*)"', files_match.group(1))) if files_match else ()
        addresses[address] = BusAddress(
            address, role, own=plain.rstrip().endswith("ebusd"), manufacturer=ident.get("MF"), ident=ident.get("ID"),
            software=ident.get("SW"), hardware=ident.get("HW"), files=files)
    version = values.pop("version", "").removeprefix("ebusd ").strip()
    signal = values.get("signal", "") == "acquired"
    return EbusdInfo(version, signal, addresses, values)


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    part: str  # "m" master data, "s" slave data
    type: str
    divisor_or_values: str
    unit: str


@dataclass(frozen=True)
class Definition:
    """One line of `find -f`."""

    direction: str  # "r", "r1".."r9", "w", "u", "uw"
    circuit: str
    name: str
    comment: str
    fields: tuple[FieldDefinition, ...]
    zz: str = ""  # target address
    pbsb: str = ""  # command bytes
    id: str = ""  # further ID bytes, in hex

    @property
    def is_read(self) -> bool:
        return self.direction.startswith("r")

    @property
    def is_passive(self) -> bool:
        return self.direction.startswith("u")


def parse_definitions(text: str) -> list[Definition]:
    definitions = []
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 8 or not row[0] or row[0].startswith(("#", "ERR")):
            continue
        cells = row[8:]
        fields = tuple(
            FieldDefinition(*(cells[i:i + 5] + [""] * 5)[:5])
            for i in range(0, len(cells), 6) if cells[i:i + 1] and cells[i])
        definitions.append(Definition(row[0], row[1], row[2], row[3], fields, row[5], row[6], row[7]))
    return definitions


def _raise_for(answer: str, command: str) -> None:
    if not answer.startswith("ERR"):
        return
    reason = answer.partition(":")[2].strip() or answer
    for text, error in (("no signal", EbusdNoSignal), ("no data stored", EbusdNoData),
                        ("element not found", EbusdNotFound), ("invalid argument", EbusdInvalidArgument)):
        if text in reason:
            raise error(reason)
    raise EbusdError(f"{command}: {reason}")


class EbusdClient:
    """Client of ebusd: reads, and the one register write. `requests` counts the commands sent, by verb."""

    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = 10.0) -> None:
        self.host, self.port, self.timeout = host, port, timeout
        self._lock = asyncio.Lock()
        self.requests: dict[str, int] = dict.fromkeys(sorted(READ_VERBS | {"write"}), 0)

    async def _command(self, text: str) -> str:
        check_command(text)
        async with self._lock:
            try:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(self.host, self.port), self.timeout)
            except (OSError, TimeoutError) as err:
                raise EbusdConnectionError(f"cannot connect to ebusd: {err or type(err).__name__}") from err
            try:
                writer.write(text.encode() + b"\n")
                await writer.drain()
                buf = b""
                while b"\n\n" not in buf:
                    chunk = await asyncio.wait_for(reader.read(65536), self.timeout)
                    if not chunk:
                        break
                    buf += chunk
            except (OSError, TimeoutError) as err:
                raise EbusdConnectionError(f"no answer from ebusd: {err or type(err).__name__}") from err
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except OSError:
                    pass
        self.requests[text.split()[0]] += 1
        answer = buf.split(b"\n\n", 1)[0].decode(errors="replace").strip()
        _raise_for(answer, text)
        return answer

    async def info(self) -> EbusdInfo:
        info = parse_info(await self._command("info"))
        if not info.version:
            raise EbusdError("the answer to `info` has no version: is this ebusd?")
        return info

    async def definitions(self, circuit: str, write: bool = False) -> list[Definition]:
        """Definitions ebusd loaded for a circuit (read and passive ones, or the write ones); empty when none."""
        try:
            return parse_definitions(await self._command(f"find -f {'-w ' if write else ''}-c {circuit}"))
        except EbusdNotFound:
            return []

    async def read_from_bus(self, circuit: str, name: str) -> tuple[str, ...]:
        """Field values of a message, asked of the device whatever ebusd holds in its cache (`read -f`)."""
        return tuple(value.strip() for value in (await self._command(f"read -f -c {circuit} {name}")).split(";"))

    async def write_register(self, circuit: str, telegram: str, source: str | None) -> str:
        """Send a register write, `telegram` = target, command, length and data in hex. ebusd sends it only when it
        matches a write definition of `circuit` it loaded. `source`: "ff", or None for ebusd's own address."""
        prefix = f"-s {source} " if source else ""
        return await self._command(f"write {prefix}-c {circuit} -h {telegram}")

    async def probe_write(self, telegram: str) -> str:
        """Ask ebusd to match a write telegram against its definitions under a circuit name no message has: it
        answers `ERR: invalid argument` when a definition matched (refused before sending), `ERR: element not
        found` when none did. Nothing is sent to the bus either way."""
        try:
            return await self._command(f"write -c {PROBE_CIRCUIT} -h {telegram}")
        except EbusdInvalidArgument:
            return "matched"
        except EbusdNotFound:
            return "not found"

    async def read(self, circuit: str, name: str, max_age: int) -> tuple[str, ...]:
        """Field values of a message. ebusd answers from its cache when its value is younger than `max_age`
        seconds, and asks the device otherwise (a passive message is never asked for)."""
        return tuple(value.strip() for value in
                     (await self._command(f"read -m {int(max_age)} -c {circuit} {name}")).split(";"))
