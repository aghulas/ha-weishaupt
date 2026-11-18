"""Polling of the registers, ordered against the read-backs of the writes.

A poll reads the devices one after the other, through the same ebusd client as the writes, and its result replaces
the data of the coordinator only when it is complete. A write made meanwhile stores its read-back at once; without
care, the poll would then put back the value it read (or copied) before the write, and the entity would show the old
value until the next poll although the bus has the new one. So every read-back is stamped, every device of a poll
is stamped before its values are copied and read, and at the end of the poll a register written after the stamp of
its device keeps the read-back.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from .registers import Device, polls_programs, program_registers, registers_of

Data = dict[str, dict[str, bytes | None]]


class RegisterReader(Protocol):
    async def read_registers(self, zz: str, registers: list[str]) -> dict[str, bytes | None]: ...


class ReadBackStamps:
    """Order of the read-backs: a counter, increased each time a read-back is stored in the data."""

    def __init__(self) -> None:
        self._count = 0
        self._stored: dict[tuple[str, str], int] = {}

    def now(self) -> int:
        """The stamp to take before reading: read-backs stored later have a higher stamp."""
        return self._count

    def store(self, data: Data, device_key: str, register: str, raw: bytes | None) -> None:
        """Store a write's read-back in the data of the coordinator, and stamp it."""
        data[device_key][register] = raw
        self._count += 1
        self._stored[(device_key, register)] = self._count

    def keep_newer(self, polled: Data, current: Data | None, read_at: dict[str, int]) -> Data:
        """In `polled`, put back every read-back stored after its device was read (`read_at`), from `current`."""
        if not current:
            return polled
        for (device_key, register), stamp in self._stored.items():
            if device_key in read_at and stamp > read_at[device_key] and register in current.get(device_key, {}):
                polled.setdefault(device_key, {})[register] = current[device_key][register]
        return polled


async def poll(client: RegisterReader, devices: list[Device], current: Callable[[], Data | None],
               stamps: ReadBackStamps, read_programs: bool) -> Data:
    """Read the registers of every device (and the time programs when asked); `current` returns the data of the
    coordinator at the time of the call. Registers not read keep their current value."""
    data: Data = {}
    read_at: dict[str, int] = {}
    for device in devices:
        read_at[device.key] = stamps.now()
        values = dict((current() or {}).get(device.key, {}))
        values.update(await client.read_registers(device.zz, registers_of(device)))
        if read_programs and polls_programs(device):
            values.update(await client.read_registers(device.zz, program_registers()))
        data[device.key] = values
    return stamps.keep_newer(data, current(), read_at)
