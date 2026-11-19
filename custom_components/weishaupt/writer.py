"""Writes of the settings the definitions prove, through the guard and the risk classes.

Created only when writes are enabled in the options of the entry. Nothing here is reached by the reader.

Path of a write (decided in `out/ha-companion-phase2.md` of the workbench):

1. gates that need no bus: writes enabled (option and switch), the setting writable, ebusd known to compute the
   run-time checksum (probe, below), the source address usable, the value on a step and in the range;
2. the setting and the settings linked to it read from the device (`read -f`): the value before, and the bounds
   narrowed by the linked ones;
3. for a write from ff, the telegram log: refused while the vendor service tool may be connected, or when the log
   is not fed; then the rate limits (`guard.py`);
4. the telegram built here (`writes.py`), sent with `write [-s ff] -c <circuit> -h <bytes>`: ebusd sends it only when
   it matches the write definition it loaded for that circuit, checksum included;
5. the setting read back from the device (`read -f`) and compared with what was sent; a value not taken over is an
   error, shown to the user. A log line and an event `weishaupt_write` for every write sent.

Risk classes: a comfort setting is written as soon as it is set; a regulation setting only after a confirmation in
a repair flow that shows the current value, the new value and the range (`repairs.py`). Structural settings never
have write conditions in the metadata and are never writable.

Capability (decision D14, without a marker in today's builds): ebusd is asked to match one write telegram under a
circuit name no message has, once with the correct checksum and once with the checksum byte of the definition. A
build with the run-time checksum matches the first and refuses it for its circuit (`ERR: invalid argument`), and
finds no definition for the second; a stock ebusd does the reverse. Neither is sent to the bus.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import datetime
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util

from .const import (
    CONF_MAX_WRITES_PER_HOUR,
    CONF_TELEGRAM_DB,
    DEFAULT_TELEGRAM_DB,
    DOMAIN,
    EVENT_WRITE,
    JOURNAL_SIZE,
    PENDING_TTL,
)
from . import clock
from .ebusd import EbusdConnectionError, EbusdError, EbusdLate
from .programs import DayError, Program, SlotSpec, format_day, parse_day, program_specs, range_of_raw, raws_of_day
from .guard import MAX_PER_HOUR, ServiceToolState, WriteGuard, WriteRefused, hourly_limit, read_service_tool_state
from .writes import WriteSpec, capability, linked, write_specs

_LOGGER = logging.getLogger(__name__)
PROBE_SETTING = "ka/BlockingTime"
CLOCK_KEY = "broadcast/Datetime"
CLOCK_REGISTER = "fe:0700"  # key of the rate limit of the clock broadcast


class ConfirmationPending(Exception):
    """A regulation setting waits for its confirmation in a repair flow."""

    def __init__(self, issue_id: str, placeholders: dict[str, str]) -> None:
        self.issue_id = issue_id
        self.placeholders = placeholders
        super().__init__(f"confirmation pending: {issue_id}")


class WriteFailed(Exception):
    """The write was sent and failed, or the device did not take the value over."""

    def __init__(self, code: str, **placeholders: object) -> None:
        self.code = code
        self.placeholders = {key: str(value) for key, value in placeholders.items()}
        super().__init__(f"{code}: {self.placeholders}")


@dataclass
class Pending:
    id: str
    key: str
    value: float
    user_id: str | None
    created: float
    placeholders: dict[str, str] = field(default_factory=dict)


def _text(spec: WriteSpec, value: float, language: str = "en") -> str:
    """A value as the device holds it: the decimals of the step (8.0 °C, not 8 °C) and the unit, or the label of the
    entry of a value list."""
    if spec.values is not None:
        raw = int(value)
        label = (spec.value_labels or {}).get(raw, {})
        return label.get(language) or label.get("en") or spec.values.get(raw, str(raw))
    return f"{value:.{spec.decimals}f}" + (f" {spec.unit}" if spec.unit else "")


# What the source address of a write is, in the words of the confirmation and of the notification.
SOURCE_TEXT = {
    "en": {"ff": "address of the vendor service tool", "31": "ebusd's own address"},
    "fr": {"ff": "adresse de l'outil de service du fabricant", "31": "adresse propre d'ebusd"},
}
DAY_NAMES = {
    "en": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
    "fr": ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"),
}
PROGRAM_FAILURE = {
    "en": ("Weekly program not written", "{program} of {device}: {written} of {total} slots written, then the "
           "write stopped: {reason}. Check the days of the program before trying again."),
    "fr": ("Programme hebdomadaire non écrit", "{program} de {device} : {written} plages écrites sur {total}, puis "
           "l'écriture s'est arrêtée : {reason}. Vérifiez les jours du programme avant de réessayer."),
}
NOTIFICATION = {
    "en": ("Confirmation needed", "{setting} of {device}: change from {current} to {requested} waits for your "
           "confirmation in [Settings → Repairs](/config/repairs). Nothing has been written. The request expires "
           "after {minutes} minutes."),
    "fr": ("Confirmation demandée", "{setting} de {device} : la modification de {current} à {requested} attend "
           "votre confirmation dans [Paramètres → Réparations](/config/repairs). Rien n'a été écrit. La demande "
           "expire après {minutes} minutes."),
}


class Writer:
    def __init__(self, hass: HomeAssistant, hub, options: dict[str, Any]) -> None:
        self.hass, self.hub = hass, hub
        self.telegram_db: str = options.get(CONF_TELEGRAM_DB) or DEFAULT_TELEGRAM_DB
        self.switch_on = False
        try:
            limit = hourly_limit(options.get(CONF_MAX_WRITES_PER_HOUR))
        except ValueError as err:  # only possible by editing the stored entry: the safe side
            _LOGGER.warning("option %s ignored (%s): %s writes per hour", CONF_MAX_WRITES_PER_HOUR, err, MAX_PER_HOUR)
            limit = MAX_PER_HOUR
        self.guard = WriteGuard(enabled=False, max_per_hour=limit)
        self.specs: dict[str, WriteSpec] = {}
        self.not_writable: dict[str, str] = {}
        self.placeholders: dict[str, str] = {}
        self.capability = "not checked"
        self.probe_answers: list[str] = []
        self.journal: deque[dict[str, Any]] = deque(maxlen=JOURNAL_SIZE)
        self.pending: dict[str, Pending] = {}
        self.programs: dict[str, Program] = {}  # programs whose slots the definitions prove writable
        self.slot_specs: dict[str, SlotSpec] = {}
        self.clock_writable = False  # the date and time broadcast: write conditions and its write definition
        self.last_clock: clock.Broadcast | None = None
        # clock and sleep of the clock broadcast, replaced by the tests
        self._now: Callable[[], datetime] = dt_util.now
        self._sleep: Callable[[float], Any] = asyncio.sleep

    # ---- start-up -------------------------------------------------------------------------------------------

    async def async_setup(self) -> None:
        """Load the write definitions ebusd has, build the specs, probe the run-time checksum. Nothing is sent to
        the bus: `find` and two probes that ebusd refuses before sending."""
        circuits = sorted({m.circuit for m in self.hub.model.messages.values()
                           if m.writable and (m.key in self.hub.usable or not (m.read or m.passive))})
        loaded = {circuit: await self.hub.client.definitions(circuit, write=True) for circuit in circuits}
        specs, refused, self.placeholders = write_specs(self.hub.model, loaded)
        self.specs = {key: spec for key, spec in specs.items() if key in self.hub.usable}
        self.not_writable = {r.key: r.reason for r in refused}
        for key in specs.keys() - self.specs.keys():
            self.not_writable[key] = "its read definition differs from the metadata"
        not_offered = {r.key for r in refused if not r.exposed}
        for key, reason in self.not_writable.items():
            if key not in not_offered:
                _LOGGER.warning("%s stays read-only: %s", key, reason)
        programs, slots, refused_programs = program_specs(self.hub.model, loaded)
        self.programs = {key: program for key, program in programs.items()
                         if all(k in self.hub.usable for day in program.slots.values() for k in day)}
        self.slot_specs = {key: spec for key, spec in slots.items()
                           if any(key in day for p in self.programs.values() for day in p.slots.values())}
        for reason in refused_programs:
            _LOGGER.warning("program stays read-only: %s", reason)
        message = self.hub.model.messages.get(CLOCK_KEY)
        self.clock_writable = bool(
            message is not None and message.write is not None and message.write.source == "31"
            and any(d.name == "Datetime" and d.direction == "w" and d.zz.lower() == "fe" and d.pbsb == "0700"
                    for d in loaded.get("broadcast", [])))
        not_offered -= {key for p in self.programs.values() for day in p.slots.values() for key in day}
        not_offered.discard(CLOCK_KEY if self.clock_writable else "")
        for key in set(self.slot_specs) | ({CLOCK_KEY} if self.clock_writable else set()):
            self.not_writable.pop(key, None)
        if not_offered:
            _LOGGER.debug("writes not offered by this version: %s", ", ".join(sorted(not_offered)))
        await self.async_probe()

    async def async_probe(self) -> str:
        if not self.specs:
            self.capability = "unknown"
            return self.capability
        # the setting of the first write test on a bus (evidence/register-write-crc.md), else the first one
        spec = self.specs.get(PROBE_SETTING) or self.specs[sorted(self.specs)[0]]
        placeholder = self.placeholders[spec.key]
        value = spec.minimum
        while spec.telegram(value)[8:10] == placeholder and value + spec.step <= spec.maximum:
            value += spec.step  # a value whose checksum differs from the placeholder: the probes must differ
        try:
            correct = await self.hub.client.probe_write(spec.telegram(value))
            other = await self.hub.client.probe_write(spec.placeholder_telegram(value, placeholder))
        except EbusdError as err:
            self.probe_answers = [str(err)]
            self.capability = "unknown"
        else:
            self.probe_answers = [correct, other]
            self.capability = capability(correct, other)
        log = _LOGGER.info if self.capability == "present" else _LOGGER.warning
        log("run-time checksum of ebusd: %s (probe of %s: %s)", self.capability, spec.key,
            ", ".join(self.probe_answers))
        return self.capability

    # ---- state ----------------------------------------------------------------------------------------------

    def set_switch(self, on: bool) -> None:
        self.switch_on = on
        self.guard.enabled = on

    def _check_static(self, spec: WriteSpec | None, key: str, value: float) -> WriteSpec:
        """Gates that need no request to the bus."""
        if not self.switch_on:
            raise WriteRefused("writes_disabled")
        if spec is None:
            raise WriteRefused("not_writable", setting=key, reason=self.not_writable.get(key, "no write conditions"))
        if self.capability == "absent":
            raise WriteRefused("capability_absent")
        if self.capability != "present":
            raise WriteRefused("capability_unknown", reason=", ".join(self.probe_answers) or self.capability)
        if not self.hub.available:
            raise WriteRefused("unavailable")
        if spec.source == "31" and self.hub.own_address != "31":
            raise WriteRefused("source_not_own", setting=key, own=self.hub.own_address or "-")
        if not spec.minimum <= value <= spec.maximum:
            raise WriteRefused("out_of_bounds", value=f"{value:g}", minimum=f"{spec.minimum:g}",
                               maximum=f"{spec.maximum:g}")
        if not spec.on_step(value):
            raise WriteRefused("off_step", value=f"{value:g}", step=f"{spec.step:g}", minimum=f"{spec.minimum:g}")
        return spec

    # ---- requests from the entities -------------------------------------------------------------------------

    async def async_request(self, key: str, value: float, user_id: str | None) -> dict[str, Any] | None:
        """A user set a setting. Comfort: written now. Regulation: a confirmation is created and
        ConfirmationPending raised."""
        spec = self._check_static(self.specs.get(key), key, value)
        if spec.risk == "comfort":
            return await self.async_write(key, value, user_id)
        return self._create_pending(spec, value, user_id)

    def _create_pending(self, spec: WriteSpec, value: float, user_id: str | None) -> None:
        for old in [p for p in self.pending.values() if p.key == spec.key]:
            self._drop_pending(old.id)
        pending = Pending(uuid.uuid4().hex[:12], spec.key, value, user_id, time.time())
        reading = self.hub.reading(spec.key)
        message = self.hub.model.messages[spec.key]
        language = self._language()
        device = self.hub.model.devices[message.device]
        pending.placeholders = {
            "setting": message.label.get(language, message.label["en"]),
            "device": device.label.get(language, device.label["en"]),
            "current": self._current(spec, reading, language),
            "requested": _text(spec, value, language),
            "minimum": _text(spec, spec.minimum, language), "maximum": _text(spec, spec.maximum, language),
            "allowed": self._allowed(spec, language),
            "step": f"{spec.step:g}",
            "address": spec.zz, "register": f"{spec.register[:2]} {spec.register[2:]}",
            "source": spec.source, "source_text": SOURCE_TEXT[language][spec.source],
            "minutes": str(PENDING_TTL // 60),
        }
        self.pending[pending.id] = pending
        issue_id = self.issue_id(pending.id)
        ir.async_create_issue(
            self.hass, DOMAIN, issue_id, is_fixable=True, is_persistent=False, severity=ir.IssueSeverity.WARNING,
            translation_key="confirm_write", translation_placeholders=pending.placeholders,
            data={"entry_id": self.hub.entry.entry_id, "pending": pending.id})
        title, text = NOTIFICATION[language]
        persistent_notification.async_create(self.hass, text.format(**pending.placeholders), title,
                                             self._notification_id(spec.key))
        _LOGGER.info("change of %s to %s waits for its confirmation (repair %s)", spec.key, value, issue_id)
        raise ConfirmationPending(issue_id, pending.placeholders)

    @staticmethod
    def _current(spec: WriteSpec, reading: tuple[str, ...] | None, language: str) -> str:
        raw = spec.raw_of_text(reading[0]) if reading and reading[0] not in ("", "-") else None
        return "-" if raw is None else _text(spec, spec.value_of(raw), language)

    @staticmethod
    def _allowed(spec: WriteSpec, language: str) -> str:
        """The values the setting takes: its range and step, or the entries of its value list."""
        if spec.values is not None:
            return ", ".join(_text(spec, raw, language) for raw in sorted(spec.values))
        word = {"en": "to", "fr": "à"}[language]
        step = {"en": "step", "fr": "pas de"}[language]
        return f"{_text(spec, spec.minimum)} {word} {_text(spec, spec.maximum)}, {step} {spec.step:g}"

    def _language(self) -> str:
        return "fr" if self.hass.config.language.startswith("fr") else "en"

    def _notification_id(self, key: str) -> str:
        return f"{DOMAIN}_confirm_{self.hub.entry.entry_id}_{key.replace('/', '_')}"

    def pending_for(self, key: str) -> Pending | None:
        return next((p for p in self.pending.values() if p.key == key), None)

    def issue_id(self, pending_id: str) -> str:
        return f"confirm_write_{self.hub.entry.entry_id}_{pending_id}"

    def _drop_pending(self, pending_id: str) -> None:
        pending = self.pending.pop(pending_id, None)
        if pending is not None:
            ir.async_delete_issue(self.hass, DOMAIN, self.issue_id(pending_id))
            persistent_notification.async_dismiss(self.hass, self._notification_id(pending.key))
            self.hub.notify(pending.key)

    def drop_all_pending(self) -> None:
        for pending_id in list(self.pending):
            self._drop_pending(pending_id)

    async def async_confirm(self, pending_id: str, user_id: str | None) -> dict[str, Any]:
        """The confirmation of a regulation setting, from the repair flow."""
        pending = self.pending.pop(pending_id, None)
        ir.async_delete_issue(self.hass, DOMAIN, self.issue_id(pending_id))
        if pending is not None:
            persistent_notification.async_dismiss(self.hass, self._notification_id(pending.key))
        if pending is None or time.time() - pending.created > PENDING_TTL:
            raise WriteFailed("expired", minutes=PENDING_TTL // 60)
        if pending.key == CLOCK_KEY:
            return await self.async_set_clock(user_id or pending.user_id)
        return await self.async_write(pending.key, pending.value, user_id or pending.user_id, confirmed=True)

    # ---- the write ------------------------------------------------------------------------------------------

    async def _read(self, spec: WriteSpec) -> tuple[tuple[str, ...], int]:
        await self.hub.async_bus_slot()
        values = await self.hub.client.read_from_bus(spec.circuit, spec.name)
        raw = spec.raw_of_values(values)
        if raw is None:
            raise EbusdError(f"answer {';'.join(values)!r}")
        return values, raw

    async def async_write(self, key: str, value: float, user_id: str | None,
                          confirmed: bool = False) -> dict[str, Any]:
        spec = self._check_static(self.specs.get(key), key, value)
        if spec.risk != "comfort" and not confirmed:
            return self._create_pending(spec, value, user_id)  # raises
        try:
            _, before = await self._read(spec)
        except EbusdError as err:
            raise WriteRefused("read_failed", setting=key, reason=err) from err
        low, high = spec.minimum, spec.maximum
        below, above = linked(spec, self.specs)
        for other, is_floor in ((below, True), (above, False)):
            if other is None:
                continue
            try:
                _, other_raw = await self._read(other)
            except EbusdError as err:
                raise WriteRefused("linked_unknown", other=other.key) from err
            bound = other.value_of(other_raw)
            low, high = (max(low, bound), high) if is_floor else (low, min(high, bound))
        source = spec.ebusd_source
        service_tool = None
        if source == "ff":
            service_tool = await self.hass.async_add_executor_job(read_service_tool_state, self.telegram_db)
        self.guard.check(spec.register_id, value, low, high, source, service_tool)

        return await self._send(spec, value, before, user_id, confirmed)

    async def _send(self, spec: WriteSpec, value: float, before: int, user_id: str | None,
                    confirmed: bool) -> dict[str, Any]:
        """Send a write the guard accepted (the caller ran `guard.check`), read it back, trace it."""
        key, source = spec.key, spec.ebusd_source
        raw = spec.raw(value)
        telegram = spec.telegram(value)
        entry: dict[str, Any] = {
            "time": time.time(), "key": key, "register": spec.register_id, "source": spec.source,
            "risk": spec.risk, "confirmed": confirmed, "user_id": user_id, "before": spec.value_of(before),
            "requested": value, "telegram": telegram, "read_back": None, "result": None,
            # the whole frame as it goes on the bus: source address first (ff, or ebusd's own address)
            "frame": f"{source or self.hub.own_address or ''}{telegram}"}
        if raw == before:
            entry["result"] = "unchanged"
            self._trace(spec, entry)
            return entry
        self.guard.record(spec.register_id, source)
        await self.hub.async_bus_slot()
        try:
            answer = await self.hub.client.write_register(spec.circuit, telegram, source)
        except EbusdError as err:
            entry["result"] = "not sent" if not isinstance(err, EbusdConnectionError) else "connection lost"
            entry["error"] = str(err)
            self._trace(spec, entry)
            raise WriteFailed("write_failed", setting=key, reason=err) from err
        entry["answer"] = answer
        try:
            values, back = await self._read(spec)
        except EbusdError as err:
            entry["result"] = "no read-back"
            entry["error"] = str(err)
            self._trace(spec, entry)
            raise WriteFailed("no_read_back", setting=key, reason=err) from err
        entry["read_back"] = spec.value_of(back)
        self.hub.store(key, values)
        entry["result"] = "ok" if back == raw else ("not taken" if back == before else "different")
        self._trace(spec, entry)
        if back != raw:
            raise WriteFailed("not_taken", setting=key, requested=_text(spec, value, self._language()),
                             read_back=_text(spec, spec.value_of(back), self._language()))
        return entry

    # ---- weekly programs (comfort: no confirmation) ---------------------------------------------------------

    def program_day(self, program: Program, day: int) -> str | None:
        """The text of a day from the last readings of its three slots, None while one is unknown."""
        ranges = []
        for key in program.day_keys(day):
            values = self.hub.reading(key)
            raw = self.slot_specs[key].raw_of_values(values) if values else None
            if raw is None:
                return None
            if (found := range_of_raw(raw)) is not None:
                ranges.append(found)
        return format_day(sorted(ranges))

    async def async_write_day(self, program_key: str, day: int, text: str, user_id: str | None) -> dict[str, Any]:
        """Write one day of a program: its three slots, read back."""
        return await self.async_set_program(program_key, {day: text}, user_id)

    async def async_set_program(self, program_key: str, days: dict[int, str],
                                user_id: str | None) -> dict[str, Any]:
        """Write days of a program (day 1 = Monday -> text). Every text is checked first, then the slots are read
        from the device; only the slots that change are written, three at most a day, 21 for a whole week. When
        they are more than the writes left within the hour, nothing is written. A failure stops the rest."""
        program = self.programs.get(program_key)
        if program is None:
            raise WriteRefused("not_writable", setting=program_key,
                               reason="the definitions prove no write of this program on this device")
        wanted: dict[int, list[int]] = {}
        language = self._language()
        for day, text in sorted(days.items()):
            try:
                wanted[day] = raws_of_day(parse_day(text))
            except DayError as err:
                raise WriteRefused(f"bad_day_{err.code}", day=DAY_NAMES[language][day - 1], part=err.part) from err
        first = self.slot_specs[program.day_keys(1)[0]]
        self._check_static(first, first.key, 0)
        changes: list[tuple[SlotSpec, int, int]] = []
        before_days: dict[int, str] = {}
        for day, raws in wanted.items():
            for key, raw in zip(program.day_keys(day), raws):
                spec = self.slot_specs[key]
                try:
                    values, before = await self._read(spec)
                except EbusdError as err:
                    raise WriteRefused("read_failed", setting=key, reason=err) from err
                self.hub.store(key, values)  # a fresh reading: the day shows it, written or not
                if raw != before:
                    changes.append((spec, raw, before))
            before_days[day] = self.program_day(program, day) or "?"
        left = self.guard.max_per_hour - self.guard.writes_last_hour()
        if len(changes) > left:
            raise WriteRefused("program_limit", needed=len(changes), left=left, limit=self.guard.max_per_hour)
        done: list[dict[str, Any]] = []
        for spec, raw, before in changes:
            service_tool = None
            if spec.ebusd_source == "ff":
                service_tool = await self.hass.async_add_executor_job(read_service_tool_state, self.telegram_db)
            try:
                self.guard.check(spec.register_id, raw, 0, 0xFFFF, spec.ebusd_source, service_tool)
                done.append(await self._send(spec, raw, before, user_id, False))
            except (WriteRefused, WriteFailed) as err:
                self._log_program(program, wanted, before_days, done, f"stopped: {err}")
                self._notify_program_failure(program, len(done), len(changes), err)
                raise WriteFailed("program_partial", written=len(done), total=len(changes), reason=err) from err
        self._log_program(program, wanted, before_days, done, "read back ok" if done else "nothing to write")
        return {"program": program_key, "written": len(done), "unchanged": 3 * len(wanted) - len(changes),
                "slots": [entry["key"] for entry in done]}

    def _log_program(self, program: Program, wanted: dict[int, list[int]], before: dict[int, str],
                     done: list[dict[str, Any]], result: str) -> None:
        """One info line per day of a program write: device, program, day, before -> after, the frames sent."""
        device = self.hub.model.devices[program.device].label["en"]
        for day, raws in wanted.items():
            keys = program.day_keys(day)
            frames = [e["frame"] for e in done if e["key"] in keys]
            after = format_day(sorted(r for r in map(range_of_raw, raws) if r is not None))
            _LOGGER.info("PROGRAM %s %s %s: %s -> %s, frames %s: %s", device, program.label["en"],
                         DAY_NAMES["en"][day - 1], before.get(day, "?"), after, ", ".join(frames) or "none", result)

    def _notify_program_failure(self, program: Program, written: int, total: int, err: Exception) -> None:
        """A short persistent notification when a program was not written, or only in part. None on success: the
        new value of the day is the feedback, and the log has the details."""
        language = self._language()
        device = self.hub.model.devices[program.device]
        title, text = PROGRAM_FAILURE[language]
        persistent_notification.async_create(
            self.hass, text.format(program=program.label.get(language, program.label["en"]),
                                   device=device.label.get(language, device.label["en"]),
                                   written=written, total=total, reason=err),
            title, f"{DOMAIN}_program_{self.hub.entry.entry_id}_{program.key.replace('/', '_')}")

    # ---- the clock (regulation: confirmation) ---------------------------------------------------------------

    async def async_clock_offset(self) -> float | None:
        """Seconds the clock master is ahead of ebusd's host clock, from its last broadcast in ebusd's cache."""
        broadcast = clock.parse_find(await self.hub.client.last_broadcast_of_clock())
        if broadcast is not None and broadcast.source != self.hub.own_address:
            self.last_clock = broadcast
        if broadcast is None:
            return None
        return clock.offset(broadcast, self.hub.own_address, self._now().replace(tzinfo=None))

    def _check_clock(self) -> None:
        if not self.switch_on:
            raise WriteRefused("writes_disabled")
        if not self.clock_writable:
            raise WriteRefused("not_writable", setting=CLOCK_KEY, reason="no write definition of the broadcast")
        if not self.hub.available:
            raise WriteRefused("unavailable")
        if self.hub.own_address != "31":
            raise WriteRefused("source_not_own", setting=CLOCK_KEY, own=self.hub.own_address or "-")

    async def async_request_clock(self, user_id: str | None) -> None:
        """The set-clock button: a regulation write, so a confirmation first. Raises ConfirmationPending."""
        self._check_clock()
        try:
            offset = await self.async_clock_offset()
        except EbusdError:
            offset = None
        for old in [p for p in self.pending.values() if p.key == CLOCK_KEY]:
            self._drop_pending(old.id)
        language = self._language()
        message = self.hub.model.messages[CLOCK_KEY]
        device = self.hub.model.devices[message.device]
        pending = Pending(uuid.uuid4().hex[:12], CLOCK_KEY, 0, user_id, time.time())
        pending.placeholders = {
            "setting": message.label.get(language, message.label["en"]),
            "device": device.label.get(language, device.label["en"]),
            "current": "-" if offset is None else f"{offset:+.0f} s",
            "requested": {"en": "Home Assistant's time", "fr": "l'heure de Home Assistant"}[language],
            "address": "fe", "register": "07 00", "source": "31",
            "source_text": SOURCE_TEXT[language]["31"], "late": f"{clock.LATE:g}",
            "minutes": str(PENDING_TTL // 60)}
        self.pending[pending.id] = pending
        issue_id = self.issue_id(pending.id)
        ir.async_create_issue(
            self.hass, DOMAIN, issue_id, is_fixable=True, is_persistent=False, severity=ir.IssueSeverity.WARNING,
            translation_key="confirm_clock", translation_placeholders=pending.placeholders,
            data={"entry_id": self.hub.entry.entry_id, "pending": pending.id})
        title, text = NOTIFICATION[language]
        persistent_notification.async_create(self.hass, text.format(**pending.placeholders), title,
                                             self._notification_id(CLOCK_KEY))
        raise ConfirmationPending(issue_id, pending.placeholders)

    async def async_set_clock(self, user_id: str | None) -> dict[str, Any]:
        """Send Home Assistant's time at second 00 of the next minute, or nothing: if the connection to ebusd is
        not free within `clock.LATE` seconds of second 00, the broadcast is given up rather than sent late."""
        self._check_clock()
        self.guard.check(CLOCK_REGISTER, 0, 0, 0, None)
        target = clock.next_minute(self._now())
        outside = self.last_clock.outside if self.last_clock else 0.0
        telegram = clock.telegram(target, outside)
        entry: dict[str, Any] = {
            "time": time.time(), "key": CLOCK_KEY, "register": CLOCK_REGISTER, "source": "31", "risk": "regulation",
            "confirmed": True, "user_id": user_id, "before": None, "requested": target.strftime("%H:%M:%S"),
            "telegram": telegram, "read_back": None, "result": None, "frame": f"31{telegram}"}
        # keep the bus quiet for the gap before second 00, so that the broadcast's turn is free when it comes
        lead = (target - self._now()).total_seconds() - self.hub.request_gap - 0.1
        if lead > 0:
            await self._sleep(lead)
        await self.hub.async_bus_slot()
        wait = (target - self._now()).total_seconds()
        if wait > 0:
            await self._sleep(wait)
        deadline = target.timestamp() + clock.LATE
        self.guard.record(CLOCK_REGISTER, None)
        try:
            entry["answer"] = await self.hub.client.write_broadcast(
                telegram, lambda: self._now().timestamp() <= deadline)
        except EbusdLate as err:
            entry["result"] = "given up"
            self._trace_clock(entry)
            raise WriteFailed("clock_late", late=f"{clock.LATE:g}") from err
        except EbusdError as err:
            entry["result"] = "not sent"
            entry["error"] = str(err)
            self._trace_clock(entry)
            raise WriteFailed("write_failed", setting=CLOCK_KEY, reason=err) from err
        entry["result"] = "sent"
        entry["late"] = round(self._now().timestamp() - target.timestamp(), 3)
        self._trace_clock(entry)
        return entry

    def _trace_clock(self, entry: dict[str, Any]) -> None:
        self.journal.append(entry)
        level = logging.INFO if entry["result"] == "sent" else logging.WARNING
        _LOGGER.log(level, "CLOCK %s (telegram %s from 31): %s", entry["requested"], entry["telegram"],
                    entry["result"])
        self.hass.bus.async_fire(EVENT_WRITE, {"entry_id": self.hub.entry.entry_id} | entry)

    def _trace(self, spec: WriteSpec, entry: dict[str, Any]) -> None:
        """A log line, an event and a line of the journal for each write attempted past the guard."""
        self.journal.append(entry)
        level = logging.INFO if entry["result"] in ("ok", "unchanged") else logging.WARNING
        _LOGGER.log(level, "WRITE %s = %s (telegram %s from %s, before %s, read back %s): %s", spec.key,
                    entry["requested"], entry["telegram"], spec.source, entry["before"], entry["read_back"],
                    entry["result"])
        self.hass.bus.async_fire(EVENT_WRITE, {"entry_id": self.hub.entry.entry_id} | entry)

    def snapshot(self) -> dict[str, Any]:
        return {
            "switch": self.switch_on, "capability": self.capability, "probe_answers": self.probe_answers,
            "telegram_db_configured": bool(self.telegram_db),
            "writable": {key: {k: v for k, v in asdict(spec).items() if k not in ("circuit", "name")}
                         for key, spec in sorted(self.specs.items())},
            "not_writable": self.not_writable, "writes_last_hour": self.guard.writes_last_hour(),
            "max_writes_per_hour": self.guard.max_per_hour,
            "pending": [{"key": p.key, "value": p.value, "age": round(time.time() - p.created)}
                        for p in self.pending.values()],
            "journal": list(self.journal),
        }
