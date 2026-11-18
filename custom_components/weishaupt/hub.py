"""Connection to ebusd, start-up checks and the paced reader.

The hub reads only: it owns the one `EbusdClient`, which refuses every command that is not `info`, `find` or
`read`. It keeps one queue for all messages and sends one request at a time, never closer together than the
configured gap. A message is requested only while an enabled entity listens to it.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CYCLIC_INTERVAL,
    CONF_REQUEST_GAP,
    CONNECTION_RETRY,
    COUNTER_INTERVAL,
    DEFAULT_CYCLIC_INTERVAL,
    DEFAULT_REQUEST_GAP,
    FAILURES_BEFORE_UNKNOWN,
    NO_SIGNAL_PAUSE,
    PASSIVE_INTERVAL,
    PASSIVE_MAX_AGE,
    PROGRAM_INTERVAL,
    RETRY_INTERVAL,
    SETTING_INTERVAL,
)
from .ebusd import (
    BusAddress,
    Definition,
    EbusdClient,
    EbusdConnectionError,
    EbusdError,
    EbusdInfo,
    EbusdNoData,
    EbusdNoSignal,
)
from .model import Device, Message, Mismatch, Model

_LOGGER = logging.getLogger(__name__)

type WeishauptConfigEntry = ConfigEntry[Hub]

# Order in which due messages are served: what is cheap and what is watched first.
_PRIORITY = {"passive": 0, "cyclic": 1}


@dataclass
class Reading:
    values: tuple[str, ...]
    when: float  # time.time()


@dataclass
class Statistics:
    """Counters for the diagnostics download."""

    bus_requests: int = 0
    cache_reads: int = 0
    failed: int = 0
    invalid_first_byte: int = 0
    no_signal: int = 0
    connection_lost: int = 0
    last_error: str | None = None
    invalid_by_message: dict[str, int] = field(default_factory=dict)


class Hub:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: EbusdClient, model: Model) -> None:
        self.hass, self.entry, self.client, self.model = hass, entry, client, model
        self.request_gap: float = entry.options.get(CONF_REQUEST_GAP, DEFAULT_REQUEST_GAP)
        self.cyclic_interval: int = entry.options.get(CONF_CYCLIC_INTERVAL, DEFAULT_CYCLIC_INTERVAL)
        self.info: EbusdInfo | None = None
        self.device_id: str | None = None  # of the hub device, set when it is registered
        self.devices: dict[str, Device] = {}
        self.unknown_slaves: list[BusAddress] = []
        self.mismatches: list[Mismatch] = []
        self.usable: set[str] = set()  # keys of the messages ebusd loaded as the metadata describes them
        self.readings: dict[str, Reading] = {}
        self.statistics = Statistics()
        self.available = True
        self._listeners: dict[str, list[CALLBACK_TYPE]] = {}
        self._availability_listeners: list[CALLBACK_TYPE] = []
        self._due: dict[str, float] = {}
        self._failures: dict[str, int] = {}
        self._last_request = 0.0
        self._wake = asyncio.Event()

    # ---- start-up -------------------------------------------------------------------------------------------

    async def async_setup(self) -> None:
        """Ask ebusd what is on the bus and what it loaded, and compare with the metadata.

        Raises EbusdError when ebusd cannot be asked. Sends `info` and one `find -f` per circuit: nothing goes to
        the bus."""
        self.info = await self.client.info()
        slaves = {a.address for a in self.info.addresses.values() if a.role == "slave" and not a.own}
        self.devices = self.model.present_devices(slaves)
        known = {c.address for d in self.model.devices.values() for c in d.circuits}
        self.unknown_slaves = [self.info.addresses[a] for a in sorted(slaves - known)]
        circuits = {c.circuit for d in self.devices.values() for c in d.circuits
                    if c.address in slaves or c.address == "fe"}
        loaded: dict[str, list[Definition]] = {}
        for circuit in sorted(circuits):
            loaded[circuit] = await self.client.definitions(circuit)
        self.mismatches = self.model.compare(circuits, loaded)
        bad = {m.key for m in self.mismatches}
        self.usable = {key for key, message in self.model.messages.items()
                       if message.circuit in circuits and key not in bad}

    def address_of(self, device: Device) -> BusAddress | None:
        """Scan result of the first circuit of the device that answers."""
        assert self.info is not None
        return next((found for c in device.circuits if (found := self.info.slave(c.address))), None)

    # ---- listeners ------------------------------------------------------------------------------------------

    @callback
    def async_listen(self, keys: tuple[str, ...], update: CALLBACK_TYPE) -> CALLBACK_TYPE:
        """Call `update` after each reading of one of the messages; they are read while someone listens."""
        for key in keys:
            self._listeners.setdefault(key, []).append(update)
            self._due.setdefault(key, 0.0)
        self._availability_listeners.append(update)
        self._wake.set()

        @callback
        def remove() -> None:
            for key in keys:
                self._listeners[key].remove(update)
                if not self._listeners[key]:
                    del self._listeners[key]
            self._availability_listeners.remove(update)

        return remove

    def reading(self, key: str) -> tuple[str, ...] | None:
        """Last valid reading of a message, None when there is none (or, for a passive message, none recent)."""
        found = self.readings.get(key)
        if found is None:
            return None
        if self.model.messages[key].passive and time.time() - found.when > PASSIVE_MAX_AGE:
            return None
        return found.values

    def interval(self, message: Message) -> int:
        if message.passive:
            return PASSIVE_INTERVAL
        if message.poll == "cyclic":
            return self.cyclic_interval
        if message.family == "program":
            return PROGRAM_INTERVAL
        if message.kind == "counter" or message.family in ("fault_history", "fault_counter") \
                or message.name == "FaultHistoryPointer":
            return COUNTER_INTERVAL
        return SETTING_INTERVAL

    # ---- the reader -----------------------------------------------------------------------------------------

    def _next(self, now: float) -> tuple[str | None, float]:
        """Key of the message to read now, or None and the delay until the next one is due."""
        due, soonest = [], None
        for key in self._listeners:
            when = self._due.get(key, 0.0)
            if when <= now:
                message = self.model.messages[key]
                poll = "passive" if message.passive else message.poll
                due.append((_PRIORITY.get(poll, 2), self.interval(message), when, key))
            elif soonest is None or when < soonest:
                soonest = when
        if due:
            return min(due)[3], 0.0
        return None, (soonest - now if soonest is not None else 3600.0)

    async def async_run(self) -> None:
        """Read the messages that are due, for as long as the config entry is loaded."""
        while True:
            key, delay = self._next(time.monotonic())
            if key is None:
                self._wake.clear()
                try:
                    await asyncio.wait_for(self._wake.wait(), delay)
                except TimeoutError:
                    pass
                continue
            message = self.model.messages[key]
            if not message.passive:
                wait = self._last_request + self.request_gap - time.monotonic()
                if wait > 0:
                    await asyncio.sleep(wait)
            pause = await self._read(message)
            if pause:
                await asyncio.sleep(pause)

    async def _read(self, message: Message) -> float:
        """Read one message and tell its listeners. Returns the seconds to stay quiet afterwards."""
        key, interval, now = message.key, self.interval(message), time.monotonic()
        max_age = PASSIVE_MAX_AGE if message.passive else interval
        if message.passive:
            self.statistics.cache_reads += 1
        else:
            self._last_request = now
            self.statistics.bus_requests += 1
        try:
            values = await self.client.read(message.circuit, message.name, max_age)
        except EbusdNoData:
            self._due[key] = now + interval  # passive message not seen yet: nothing wrong
            return 0.0
        except EbusdConnectionError as err:
            self.statistics.connection_lost += 1
            self.statistics.last_error = str(err)
            self._set_available(False, f"ebusd cannot be reached: {err}")
            self._due[key] = now + CONNECTION_RETRY
            return CONNECTION_RETRY
        except EbusdNoSignal as err:
            self.statistics.no_signal += 1
            self.statistics.last_error = str(err)
            self._set_available(False, "ebusd has no signal on the bus")
            self._due[key] = now + NO_SIGNAL_PAUSE
            return NO_SIGNAL_PAUSE
        except EbusdError as err:
            self._set_available(True)
            self._failed(message, str(err))
            return 0.0
        self._set_available(True)
        guard = message.guard
        if len(values) != len(message.fields):
            self._failed(message, f"{len(values)} values for {len(message.fields)} fields")
            return 0.0
        if guard is not None and values[guard.index] != "0":
            # first answer byte not 0: no value of this reading is valid (notice of the definitions release)
            self.statistics.invalid_first_byte += 1
            self.statistics.invalid_by_message[key] = self.statistics.invalid_by_message.get(key, 0) + 1
            _LOGGER.debug("%s: reading dropped, first answer byte %s", key, values[guard.index])
            self._due[key] = now + RETRY_INTERVAL
            return 0.0
        self._failures.pop(key, None)
        self.readings[key] = Reading(values, time.time())
        self._due[key] = now + interval
        self._notify(key)
        return 0.0

    def _failed(self, message: Message, reason: str) -> None:
        key = message.key
        self.statistics.failed += 1
        self.statistics.last_error = f"{key}: {reason}"
        self._failures[key] = self._failures.get(key, 0) + 1
        _LOGGER.debug("%s: reading failed (%s)", key, reason)
        self._due[key] = time.monotonic() + RETRY_INTERVAL
        if self._failures[key] == FAILURES_BEFORE_UNKNOWN and self.readings.pop(key, None) is not None:
            self._notify(key)

    def _notify(self, key: str) -> None:
        for update in list(self._listeners.get(key, ())):
            update()

    def _set_available(self, available: bool, reason: str = "") -> None:
        if available == self.available:
            return
        self.available = available
        if available:
            _LOGGER.info("ebusd answers again")
        else:
            _LOGGER.warning("%s; the values are unavailable until it answers", reason)
        for update in list(self._availability_listeners):
            update()

    def snapshot(self) -> dict[str, object]:
        """State of the reader, for the diagnostics download."""
        now = time.monotonic()
        return {
            "request_gap": self.request_gap,
            "cyclic_interval": self.cyclic_interval,
            "available": self.available,
            "messages_listened": len(self._listeners),
            "messages_read": len(self.readings),
            "due_now": sum(1 for key in self._listeners if self._due.get(key, 0.0) <= now),
            "time": dt_util.utcnow().isoformat(),
        }
