"""Connection to ebusd, start-up checks and the paced reader.

The hub reads: it owns the one `EbusdClient`, which refuses every command that is not `info`, `find`, `read` or
the one register write of `writes.py` (sent by `writer.py`, never by the hub). It keeps one queue for all messages
and sends one request at a time, never closer together than the configured gap; the writer takes its requests
from the same pacing. A message is requested only while an enabled entity listens to it.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

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

# Order in which due messages are served: what is cheap and what is watched first. Passive messages (ebusd's
# cache), live values, then what an entity that sets a value shows (numbers and selects, then the slots of program
# days: within one class the shorter interval goes first), then everything else.
_PRIORITY = {"passive": 0, "cyclic": 1}
SETTING_PRIORITY = 2
OTHER_PRIORITY = 3
ONCE_PRIORITY = 4  # read once for the panel: after everything an entity waits for
# The first pass after a set-up: every message an enabled entity listens to is read once from the device (`read
# -m 0`: ebusd, which may have stayed up, would otherwise answer from its own cache, with a value up to a day old for
# the programs). Until every one of them has been asked once, a message already read is asked again only when its
# last reading is older than this, so that live values are not left for the whole pass and do not hold it up.
REPEAT_DURING_FIRST_PASS = 900
FIRST_READ_FROM_DEVICE = True  # False: the behaviour of 0.3.0rc5 (first pass answered from ebusd's cache), for the bench


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


@dataclass
class ReadJob:
    """Reads asked from the panel for a menu, a device or the installation, followed until all are asked."""

    id: str
    keys: tuple[str, ...]
    started: float
    stopped: int = 0
    ended: float | None = None


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
        # told of each reading without causing any (the panel): key of the message, or None for the availability
        self._observers: list[Callable[[str | None], None]] = []
        self._closing: list[CALLBACK_TYPE] = []  # told when the entry unloads (the panel subscribes again)
        self._once: set[str] = set()  # asked once for the panel although no entity listens (`async_read_once`)
        # reads asked from the panel's tables (`async_read_job`): id -> the keys it queued, when it started; dropped
        # with the hub at a reload
        self.read_jobs: dict[str, ReadJob] = {}
        self._job_of: dict[str, str] = {}  # key queued once -> the job that queued it
        self._job_counter = 0
        self.circuits: set[str] = set()  # circuits of the devices present, whose definitions were compared
        self.named_entities: set[str] = set()  # unique ids of the entities named from the metadata
        self._due: dict[str, float] = {}
        self._failures: dict[str, int] = {}
        self._last_request = 0.0
        self._wake = asyncio.Event()
        self._urgent: set[str] = set()  # messages of an entity just enabled: read first
        self._priority: dict[str, int] = {}  # class asked for by a listener
        self.restored: set[str] = set()  # messages shown from before a reload, until read again
        self._asked: set[str] = set()  # messages asked once since the set-up (the first pass)
        self.first_pass_done: float | None = None  # time.time() when the first pass ended
        # messages listened to when the entry was last unloaded (None at the first set-up since Home Assistant
        # started): kept by __init__.py across a reload
        self.previously_listened: set[str] | None = None
        # messages of entities the migration of the entry has just enabled: read first at the first set-up
        self.urgent_at_start: set[str] = set()
        self.writer = None  # writer.Writer, when writes are enabled in the options
        # whether ebusd computes the run-time checksum, probed at every set-up whether writes are enabled or not
        # (the writer's probe when there is a writer): which ebusd build answers, found without sending anything to
        # the bus
        self.build_capability = "not checked"
        self.build_probe_answers: list[str] = []
        # where the metadata comes from (metadata_file.py), and the names the bundled translations hold when it is
        # not the bundled copy: an entity whose name they do not hold is not created (see `named`)
        self.metadata_source = "bundled"
        self.metadata_refused: dict[str, str] = {}
        self.translated: set[tuple[str, str]] | None = None
        self.not_named: set[str] = set()
        self.named_from_metadata: set[str] = set()
        self.scan_incomplete: list[str] = []  # what ebusd has not scanned or loaded yet (async_setup)

    # ---- start-up -------------------------------------------------------------------------------------------

    async def async_setup(self, expected: set[str] | None = None) -> None:
        """Ask ebusd what is on the bus and what it loaded, and compare with the metadata.

        `expected`: the devices seen at an earlier start (the device registry of the entry). One of them not on
        the bus, or a device on the bus whose definitions ebusd has not loaded yet, means ebusd is still scanning
        (after its restart): `scan_incomplete` names them, and the entry waits (__init__.py).

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
        self.scan_incomplete = sorted(
            [f"{device_id}: not on the bus yet" for device_id in (expected or set()) - set(self.devices)
             if device_id in self.model.devices]
            + [f"{c.circuit} ({c.address}): definitions not loaded yet"
               for d in self.devices.values() for c in d.circuits
               if c.address != "fe" and c.address in slaves
               and (not loaded.get(c.circuit) or not (self.info.slave(c.address) or BusAddress(c.address, "slave")).files)])
        self.mismatches = self.model.compare(circuits, loaded)
        bad = {m.key for m in self.mismatches}
        self.circuits = circuits
        self.usable = {key for key, message in self.model.messages.items()
                       if message.circuit in circuits and key not in bad and (message.read or message.passive)}

    def named(self, platform: str, key: str, device: str | None = None,
              name: dict[str, str] | None = None) -> bool:
        """Whether this entity has a name. Always true with the bundled metadata. With a newer metadata file, the
        translations shipped with the integration name it first; when they do not hold its key, the label the
        metadata gives it (`name`, English and French) is its name (`untranslated`). An entity with neither is not
        created until a release of the integration brings its name: no entity without a name."""
        if self.translated is None:
            return True
        if (platform, key) in self.translated and (device is None or ("device", device) in self.translated):
            return True
        if name:
            self.named_from_metadata.add(f"{platform}.{key}")
            return True
        self.not_named.add(f"{platform}.{key}")
        return False

    def untranslated(self, platform: str, key: str) -> bool:
        """True when a newer metadata file is in use and the shipped translations do not hold this key."""
        return self.translated is not None and (platform, key) not in self.translated

    def label(self, text: dict[str, str]) -> str:
        """A label of the metadata in the language of Home Assistant, English when it has none in that language."""
        return text.get(self.hass.config.language.split("-")[0]) or text["en"]

    @property
    def capability(self) -> str:
        """"present", "absent", "unknown" or "not checked": the run-time checksum of the ebusd in use."""
        return self.writer.capability if self.writer is not None else self.build_capability

    @property
    def own_address(self) -> str | None:
        """Master address of ebusd itself, from `info`."""
        if self.info is None:
            return None
        return next((a.address for a in self.info.addresses.values() if a.own and a.role == "master"), None)

    async def async_bus_slot(self) -> None:
        """Wait until a request may go to the bus without breaking the gap, and take that slot. The reader and the
        writer share it."""
        wait = self._last_request + self.request_gap - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_request = time.monotonic()
        self.statistics.bus_requests += 1

    def store(self, key: str, values: tuple[str, ...]) -> None:
        """A reading obtained outside the reader (the read-back of a write): keep it and tell the listeners."""
        self.restored.discard(key)
        self.readings[key] = Reading(values, time.time())
        self._failures.pop(key, None)
        self._notify(key)

    def address_of(self, device: Device) -> BusAddress | None:
        """Scan result of the first circuit of the device that answers."""
        assert self.info is not None
        return next((found for c in device.circuits if (found := self.info.slave(c.address))), None)

    # ---- listeners ------------------------------------------------------------------------------------------

    @callback
    def async_listen(self, keys: tuple[str, ...], update: CALLBACK_TYPE,
                     priority: int | None = None) -> CALLBACK_TYPE:
        """Call `update` after each reading of one of the messages; they are read while someone listens.

        A message nobody listened to before the last reload of the entry belongs to an entity the user has just
        enabled (Home Assistant reloads the entry for it): it is read before any other, once, instead of after the
        whole first fill.

        `priority`: the class the listener asks for (SETTING_PRIORITY for the entities that set a value); a message
        is served in the most urgent class any of its listeners asks for. It changes the order, not the load."""
        for key in keys:
            self._listeners.setdefault(key, []).append(update)
            if priority is not None:
                self._priority[key] = min(priority, self._priority.get(key, priority))
            self._due.setdefault(key, 0.0)
            if (self.previously_listened is not None and key not in self.previously_listened
                    and key not in self.readings) or key in self.urgent_at_start:
                self._urgent.add(key)
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
        in_first_pass = self.first_pass_done is None and REPEAT_DURING_FIRST_PASS > 0
        wall = time.time()
        for key in [*self._listeners, *(k for k in self._once if k not in self._listeners)]:
            when = self._due.get(key, 0.0)
            if when <= now:
                message = self.model.messages[key]
                poll = "passive" if message.passive else message.poll
                priority = ONCE_PRIORITY if key in self._once else -1 if key in self._urgent else min(
                    _PRIORITY.get(poll, OTHER_PRIORITY), self._priority.get(key, OTHER_PRIORITY))
                # during the first pass, what was not asked yet goes before a repeat that is not overdue
                repeat = in_first_pass and key in self._asked and not message.passive and (
                    (reading := self.readings.get(key)) is None or wall - reading.when < REPEAT_DURING_FIRST_PASS)
                due.append((repeat, priority, self.interval(message), when, key))
            elif soonest is None or when < soonest:
                soonest = when
        if due:
            return min(due)[4], 0.0
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
            in_job = key in self._job_of
            pause = await self._read(message)
            if in_job:  # a read the panel follows was asked, whatever came of it: its progress moves on
                for observer in list(self._observers):
                    observer(None)
            if pause:
                await asyncio.sleep(pause)

    async def _read(self, message: Message) -> float:
        """Read one message and tell its listeners. Returns the seconds to stay quiet afterwards."""
        key, interval, now = message.key, self.interval(message), time.monotonic()
        self._urgent.discard(key)
        self._once.discard(key)  # asked once for the panel: not again, even when it fails
        self._job_of.pop(key, None)
        first = key not in self._asked
        self._asked.add(key)
        if self.first_pass_done is None and self._asked >= set(self._listeners):
            self.first_pass_done = time.time()
            _LOGGER.info("first pass done: %d messages asked once from the device", len(self._asked))
        # the first reading after a set-up comes from the device, not from ebusd's cache
        max_age = PASSIVE_MAX_AGE if message.passive else (0 if first and FIRST_READ_FROM_DEVICE else interval)
        if message.passive:
            self.statistics.cache_reads += 1
        else:
            self._last_request = now
            self.statistics.bus_requests += 1
        try:
            values = await self.client.read(message.circuit, message.name, max_age)
        except EbusdNoData:
            self._done(message)
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
        self._done(message)
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
        self.restored.discard(key)
        self.readings[key] = Reading(values, time.time())
        self._due[key] = now + interval
        self._notify(key)
        return 0.0

    def _done(self, message: Message) -> None:
        """The gap counts from the end of a bus request: a request that waited for the connection (another command
        of the integration on it) does not shorten the next gap."""
        if not message.passive:
            self._last_request = time.monotonic()

    def _failed(self, message: Message, reason: str) -> None:
        key = message.key
        self.statistics.failed += 1
        self.statistics.last_error = f"{key}: {reason}"
        self._failures[key] = self._failures.get(key, 0) + 1
        _LOGGER.debug("%s: reading failed (%s)", key, reason)
        self._due[key] = time.monotonic() + RETRY_INTERVAL
        if self._failures[key] == FAILURES_BEFORE_UNKNOWN and self.readings.pop(key, None) is not None:
            self._notify(key)

    def notify(self, key: str) -> None:
        """Tell the listeners of a message that something about it changed (a pending change withdrawn)."""
        self._notify(key)

    def _notify(self, key: str) -> None:
        for update in list(self._listeners.get(key, ())):
            update()
        for observer in list(self._observers):
            observer(key)

    @callback
    def async_on_close(self, closing: CALLBACK_TYPE) -> CALLBACK_TYPE:
        """Call `closing` when the entry unloads: an observer of this hub is told to look for the new one."""
        self._closing.append(closing)

        @callback
        def remove() -> None:
            if closing in self._closing:
                self._closing.remove(closing)

        return remove

    @callback
    def async_close(self) -> None:
        for closing in list(self._closing):
            closing()
        self._closing.clear()

    def to_read_once(self, keys: tuple[str, ...] | list[str]) -> list[str]:
        """What `async_read_once` would really ask: usable, not read by an enabled entity, not already queued."""
        return [key for key in keys if key in self.usable and key not in self._listeners and key not in self._once]

    def queue_state(self) -> dict[str, Any]:
        """What a request asked now waits behind: the messages due now, whether the first pass after a start is
        still running, and the gap between two requests."""
        now = time.monotonic()
        ahead = sum(1 for key in [*self._listeners, *self._once] if self._due.get(key, 0.0) <= now
                    and not self.model.messages[key].passive)
        return {"ahead": ahead, "first_pass": self.first_pass_done is None, "gap": max(self.request_gap, 1.0)}

    @callback
    def async_read_once(self, keys: tuple[str, ...]) -> int:
        """Read these messages once although no entity listens to them (a program the panel shows), at the pace of
        the reader and after what entities wait for. Returns how many are queued."""
        queued = self.to_read_once(keys)
        for key in queued:
            self._once.add(key)
            self._due[key] = 0.0
        self._wake.set()
        return len(queued)

    @callback
    def async_read_job(self, keys: list[str]) -> ReadJob:
        """Read these messages once, as `async_read_once`, as one job the panel follows and can stop."""
        queued = self.to_read_once(keys)
        for old in [j.id for j in self.read_jobs.values() if j.ended is not None and time.time() - j.ended > 600]:
            del self.read_jobs[old]
        self._job_counter += 1
        job = ReadJob(f"read{self._job_counter}", tuple(queued), time.time())
        self.read_jobs[job.id] = job
        self.async_read_once(tuple(queued))
        for key in queued:
            self._job_of[key] = job.id
        if not queued:
            job.ended = time.time()
        return job

    def job_progress(self, job: ReadJob) -> dict[str, Any]:
        """How far a job is: asked (done), with a value read since it started (read), stopped, ended."""
        left = sum(1 for key in job.keys if self._job_of.get(key) == job.id)
        read = sum(1 for key in job.keys if (r := self.readings.get(key)) is not None and r.when >= job.started)
        if left == 0 and job.ended is None:
            job.ended = time.time()
        return {"id": job.id, "total": len(job.keys), "done": len(job.keys) - left - job.stopped, "read": read,
                "stopped": job.stopped, "ended": job.ended is not None}

    @callback
    def async_stop_job(self, job_id: str) -> ReadJob | None:
        """Withdraw what a job has not asked yet; what is being asked now finishes. Nothing else is touched: the
        job queued only keys nobody else had queued."""
        job = self.read_jobs.get(job_id)
        if job is None:
            return None
        stopped = [key for key in job.keys if self._job_of.get(key) == job.id]
        for key in stopped:
            self._once.discard(key)
            del self._job_of[key]
        job.stopped += len(stopped)
        job.ended = job.ended or time.time()
        for observer in list(self._observers):
            observer(None)
        return job

    @callback
    def async_observe(self, observer: Callable[[str | None], None]) -> CALLBACK_TYPE:
        """Call `observer` with the key of each message read (None when the availability changes). Unlike
        `async_listen`, observing asks nothing: what nobody listens to is not read (the panel shows it as such)."""
        self._observers.append(observer)

        @callback
        def remove() -> None:
            self._observers.remove(observer)

        return remove

    def _set_available(self, available: bool, reason: str = "") -> None:
        if available == self.available:
            return
        self.available = available
        for observer in list(self._observers):
            observer(None)
        if available:
            _LOGGER.info("ebusd answers again")
        else:
            _LOGGER.warning("%s; the values are unavailable until it answers", reason)
        for update in list(self._availability_listeners):
            update()

    def listened(self) -> set[str]:
        return set(self._listeners)

    def restore(self, readings: dict[str, Reading]) -> None:
        """Readings kept across a reload of the entry: still valid ones are shown at once, so that nothing reads
        unknown, and every message an enabled entity listens to is read again in the first pass, in its usual order
        (live values, settings, program days, the rest). Waiting for the end of their interval would show a value
        changed at the device itself up to a day late (the programs are read once a day). Messages no enabled
        entity listens to are not read at all, as before."""
        now = time.time()
        for key, reading in readings.items():
            if key not in self.usable:
                continue
            if 0 <= now - reading.when < self.interval(self.model.messages[key]):
                self.readings[key] = reading
                self.restored.add(key)

    def snapshot(self) -> dict[str, object]:
        """State of the reader, for the diagnostics download."""
        now = time.monotonic()
        return {
            "request_gap": self.request_gap,
            "cyclic_interval": self.cyclic_interval,
            "available": self.available,
            "messages_listened": len(self._listeners),
            "messages_read": len(self.readings),
            "restored_not_read_again": len(self.restored),
            "first_pass": {"asked": len(self._asked & set(self._listeners)), "listened": len(self._listeners),
                           "done": self.first_pass_done},
            "due_now": sum(1 for key in self._listeners if self._due.get(key, 0.0) <= now),
            "time": dt_util.utcnow().isoformat(),
        }
