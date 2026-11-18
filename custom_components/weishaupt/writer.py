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

import logging
import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import (
    CONF_TELEGRAM_DB,
    DEFAULT_TELEGRAM_DB,
    DOMAIN,
    EVENT_WRITE,
    JOURNAL_SIZE,
    PENDING_TTL,
)
from .ebusd import EbusdConnectionError, EbusdError
from .guard import ServiceToolState, WriteGuard, WriteRefused, read_service_tool_state
from .writes import WriteSpec, capability, linked, write_specs

_LOGGER = logging.getLogger(__name__)
PROBE_SETTING = "ka/BlockingTime"


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


def _text(spec: WriteSpec, value: float) -> str:
    return f"{value:g}" + (f" {spec.unit}" if spec.unit else "")


class Writer:
    def __init__(self, hass: HomeAssistant, hub, options: dict[str, Any]) -> None:
        self.hass, self.hub = hass, hub
        self.telegram_db: str = options.get(CONF_TELEGRAM_DB) or DEFAULT_TELEGRAM_DB
        self.switch_on = False
        self.guard = WriteGuard(enabled=False)
        self.specs: dict[str, WriteSpec] = {}
        self.not_writable: dict[str, str] = {}
        self.placeholders: dict[str, str] = {}
        self.capability = "not checked"
        self.probe_answers: list[str] = []
        self.journal: deque[dict[str, Any]] = deque(maxlen=JOURNAL_SIZE)
        self.pending: dict[str, Pending] = {}

    # ---- start-up -------------------------------------------------------------------------------------------

    async def async_setup(self) -> None:
        """Load the write definitions ebusd has, build the specs, probe the run-time checksum. Nothing is sent to
        the bus: `find` and two probes that ebusd refuses before sending."""
        circuits = sorted({m.circuit for m in self.hub.model.messages.values()
                           if m.writable and m.key in self.hub.usable})
        loaded = {circuit: await self.hub.client.definitions(circuit, write=True) for circuit in circuits}
        specs, refused, self.placeholders = write_specs(self.hub.model, loaded)
        self.specs = {key: spec for key, spec in specs.items() if key in self.hub.usable}
        self.not_writable = {r.key: r.reason for r in refused}
        for key in specs.keys() - self.specs.keys():
            self.not_writable[key] = "its read definition differs from the metadata"
        for key, reason in self.not_writable.items():
            _LOGGER.warning("%s stays read-only: %s", key, reason)
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
        language = "fr" if self.hass.config.language.startswith("fr") else "en"
        device = self.hub.model.devices[message.device]
        pending.placeholders = {
            "setting": message.label.get(language, message.label["en"]),
            "device": device.label.get(language, device.label["en"]),
            "current": _text(spec, float(reading[0])) if reading and reading[0] not in ("", "-") else "-",
            "requested": _text(spec, value),
            "minimum": _text(spec, spec.minimum), "maximum": _text(spec, spec.maximum),
            "minutes": str(PENDING_TTL // 60),
        }
        self.pending[pending.id] = pending
        issue_id = self.issue_id(pending.id)
        ir.async_create_issue(
            self.hass, DOMAIN, issue_id, is_fixable=True, is_persistent=False, severity=ir.IssueSeverity.WARNING,
            translation_key="confirm_write", translation_placeholders=pending.placeholders,
            data={"entry_id": self.hub.entry.entry_id, "pending": pending.id})
        _LOGGER.info("change of %s to %s waits for its confirmation (repair %s)", spec.key, value, issue_id)
        raise ConfirmationPending(issue_id, pending.placeholders)

    def issue_id(self, pending_id: str) -> str:
        return f"confirm_write_{self.hub.entry.entry_id}_{pending_id}"

    def _drop_pending(self, pending_id: str) -> None:
        if self.pending.pop(pending_id, None) is not None:
            ir.async_delete_issue(self.hass, DOMAIN, self.issue_id(pending_id))

    def drop_all_pending(self) -> None:
        for pending_id in list(self.pending):
            self._drop_pending(pending_id)

    async def async_confirm(self, pending_id: str, user_id: str | None) -> dict[str, Any]:
        """The confirmation of a regulation setting, from the repair flow."""
        pending = self.pending.pop(pending_id, None)
        ir.async_delete_issue(self.hass, DOMAIN, self.issue_id(pending_id))
        if pending is None or time.time() - pending.created > PENDING_TTL:
            raise WriteFailed("expired", minutes=PENDING_TTL // 60)
        return await self.async_write(pending.key, pending.value, user_id or pending.user_id, confirmed=True)

    # ---- the write ------------------------------------------------------------------------------------------

    async def _read(self, spec: WriteSpec) -> tuple[tuple[str, ...], int]:
        await self.hub.async_bus_slot()
        values = await self.hub.client.read_from_bus(spec.circuit, spec.name)
        raw = spec.raw_of_text(values[0]) if values else None
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

        raw = spec.raw(value)
        telegram = spec.telegram(value)
        entry: dict[str, Any] = {
            "time": time.time(), "key": key, "register": spec.register_id, "source": spec.source,
            "risk": spec.risk, "confirmed": confirmed, "user_id": user_id, "before": spec.value_of(before),
            "requested": value, "telegram": telegram, "read_back": None, "result": None}
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
            raise WriteFailed("not_taken", setting=key, requested=f"{value:g}", read_back=f"{spec.value_of(back):g}")
        return entry

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
            "pending": [{"key": p.key, "value": p.value, "age": round(time.time() - p.created)}
                        for p in self.pending.values()],
            "journal": list(self.journal),
        }
