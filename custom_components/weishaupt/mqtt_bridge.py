"""MQTT transport for the Weishaupt companion: consumes `weishaupt2mqtt` topics over Home Assistant's MQTT."""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.util import dt as dt_util

from .const import DEFAULT_BASE_TOPIC, DOMAIN
from .ebusd import BusAddress, EbusdInfo
from .guard import WriteRefused
from .hub import Hub, WeishauptConfigEntry
from .model import Message, Model, single_setting
from .programs import (
    SLOTS,
    DayError,
    Program,
    SlotSpec,
    format_day,
    parse_day,
)
from .writer import DAY_NAMES, WriteFailed, Writer, _text
from .writes import RISKS, TYPES, WriteSpec, linked

_LOGGER = logging.getLogger(__name__)
MQTT_STARTUP_TIMEOUT = 8.0
MQTT_WRITE_TIMEOUT = 20.0
BRIDGE_PROBE_TIMEOUT = 5.0  # seconds the config flow waits for the retained `bridge/state` and `bridge/info`


def valid_base_topic(topic: str) -> bool:
    """Whether `topic` can be the base topic of a bridge: a topic to publish under, so without wildcard."""
    try:
        mqtt.valid_publish_topic(topic)
    except vol.Invalid:
        return False
    return True


async def async_probe_bridge(hass: HomeAssistant, base_topic: str) -> str | None:
    """Whether a `weishaupt2mqtt` bridge is online on this base topic: None, or the error to show in the flow.

    `mqtt_not_available`: Home Assistant's MQTT integration is not set up; `bridge_offline`: `bridge/state` reads
    `offline` (the last will of a bridge that stopped); `no_bridge`: `bridge/state` did not read `online` or no
    `bridge/info` arrived in time. Both topics are retained: a running bridge answers at once. Subscribes only;
    nothing is published."""
    if not await mqtt.async_wait_for_mqtt_client(hass):
        return "mqtt_not_available"
    seen: dict[str, Any] = {}
    done = asyncio.Event()

    @callback
    def on_state(msg: mqtt.ReceiveMessage) -> None:
        seen["state"] = str(msg.payload).strip().lower()
        if "info" in seen:
            done.set()

    @callback
    def on_info(msg: mqtt.ReceiveMessage) -> None:
        try:
            data = json.loads(msg.payload)
        except (ValueError, TypeError):
            return
        if isinstance(data, dict):
            seen["info"] = data
            if "state" in seen:
                done.set()

    unsubs = [await mqtt.async_subscribe(hass, f"{base_topic}/bridge/state", on_state, qos=1),
              await mqtt.async_subscribe(hass, f"{base_topic}/bridge/info", on_info, qos=1)]
    try:
        await asyncio.wait_for(done.wait(), timeout=BRIDGE_PROBE_TIMEOUT)
    except TimeoutError:
        pass
    finally:
        for unsub in unsubs:
            unsub()
    if seen.get("state") == "offline":
        return "bridge_offline"
    if seen.get("state") != "online" or "info" not in seen:
        return "no_bridge"
    return None


def _decode_mqtt_message(message: Message, val: Any) -> tuple[str, ...]:
    """Turn a decoded JSON value from `weishaupt2mqtt` (`<circuit>/state`) into the field tuple `Hub.reading` holds."""
    usable = [f for f in message.fields if not f.skip and not f.guard]
    out: list[str] = []
    for fld in message.fields:
        if fld.guard:
            out.append("0")
        elif fld.skip:
            out.append("")
        else:
            if len(usable) == 1 and not isinstance(val, dict):
                raw_v = val
            elif isinstance(val, dict):
                raw_v = val.get(fld.name)
            else:
                raw_v = None
            if raw_v is None:
                out.append(str(fld.absent) if fld.absent is not None else "-")
            else:
                out.append(str(raw_v))
    return tuple(out)


def _mqtt_write_specs(model: Model, circuits: set[str], usable: set[str]) -> tuple[dict[str, WriteSpec], dict[str, str]]:
    """Build `WriteSpec` objects purely from metadata for circuits present on the MQTT bridge."""
    specs: dict[str, WriteSpec] = {}
    not_writable: dict[str, str] = {}
    for message in model.messages.values():
        if message.circuit not in circuits or message.write is None:
            continue
        if message.shared_with:
            not_writable[message.key] = f"kept by {message.shared_with}: changed there"
            continue
        if single_setting(message) is None:
            continue
        if message.key not in usable:
            not_writable[message.key] = "not usable"
            continue
        conditions = message.write
        if conditions.risk not in RISKS or conditions.source not in ("ff", "31"):
            not_writable[message.key] = f"unsupported risk/source ({conditions.risk}/{conditions.source})"
            continue
        fields = [f for f in message.fields if f.shown]
        if len(fields) != 1 or fields[0].type not in TYPES:
            not_writable[message.key] = "not one 16-bit number"
            continue
        fld = fields[0]
        divisor = fld.divisor or 1
        reg_id = message.name
        if fld.values:
            values = {int(raw): name for raw, name in fld.values.items()}
            labels = {int(raw): label for raw, label in (fld.value_labels or {}).items()}
            specs[message.key] = WriteSpec(
                message.key, message.circuit, message.name, message.address.lower(),
                reg_id, fld.type, 1, float(min(values)), float(max(values)), 1.0, None,
                conditions.source, conditions.risk, conditions.proof, tuple(conditions.open),
                "definitions", None, values, labels,
            )
            continue
        minimum, maximum, step, bounds_from = fld.minimum, fld.maximum, fld.step, "definitions"
        if minimum is None or maximum is None:
            if conditions.minimum is None or conditions.maximum is None:
                not_writable[message.key] = "no range"
                continue
            minimum, maximum, step, bounds_from = conditions.minimum, conditions.maximum, conditions.step, "metadata"
        if step is None:
            step = 1.0 if divisor == 1 else 1.0 / divisor
        specs[message.key] = WriteSpec(
            message.key, message.circuit, message.name, message.address.lower(),
            reg_id, fld.type, divisor, float(minimum), float(maximum), float(step), fld.unit,
            conditions.source, conditions.risk, conditions.proof, tuple(conditions.open),
            bounds_from, conditions.range_source if bounds_from == "metadata" else None,
            below=conditions.below, above=conditions.above,
        )
    return specs, not_writable


def _mqtt_program_specs(model: Model, circuits: set[str], usable: set[str]) -> tuple[dict[str, Program], dict[str, SlotSpec]]:
    """Build writable `Program` and `SlotSpec` objects purely from metadata for circuits present on MQTT."""
    programs: dict[str, Program] = {}
    slot_specs: dict[str, SlotSpec] = {}
    for group in model.groups.values():
        if group.family != "program" or group.circuit not in circuits:
            continue
        members = [model.messages[k] for k in group.members if k in model.messages]
        if len(members) != len(group.members):
            continue
        if any(m.shared_with for m in members):
            continue
        if not all(m.write is not None and m.write.risk == "comfort" for m in members):
            continue
        if not all(m.key in usable for m in members):
            continue
        slots: dict[int, list[str]] = {}
        group_specs: dict[str, SlotSpec] = {}
        ok = True
        for message in members:
            cond = message.write
            assert cond is not None
            pos = message.position or {}
            day, slot_num = pos.get("day"), pos.get("slot")
            if not isinstance(day, int) or not isinstance(slot_num, int) or not 1 <= slot_num <= SLOTS:
                ok = False
                break
            slots.setdefault(day, [""] * SLOTS)[slot_num - 1] = message.key
            group_specs[message.key] = SlotSpec(
                message.key, message.circuit, message.name, message.address.lower(),
                message.name, "SLOT", 1, 0.0, 65535.0, 1.0, None,
                cond.source, cond.risk, cond.proof, tuple(cond.open), "definitions",
            )
        if not ok or len(slots) != 7 or any("" in d for d in slots.values()):
            continue
        slot_specs.update(group_specs)
        programs[group.key] = Program(
            group.key, group.circuit, group.id, group.device, group.label,
            {day: tuple(keys) for day, keys in sorted(slots.items())},
        )
    return programs, slot_specs


class MqttHub(Hub):
    """Push-based Hub backed by Home Assistant's MQTT integration and `weishaupt2mqtt`."""

    def __init__(self, hass: HomeAssistant, entry: WeishauptConfigEntry, base_topic: str, model: Model) -> None:
        super().__init__(hass, entry, None, model)  # type: ignore[arg-type]
        self.base_topic = (base_topic or DEFAULT_BASE_TOPIC).strip("/") or DEFAULT_BASE_TOPIC
        self._unsubs: list[CALLBACK_TYPE] = []
        self._info_event = asyncio.Event()
        self.bridge_info: dict[str, Any] = {}
        self._bridge_state: str | None = None
        self._started_up = False
        self._stop_event = asyncio.Event()

    async def async_setup(self, expected: set[str] | None = None) -> None:
        """Subscribe to `weishaupt2mqtt` topics and wait for the retained `bridge/info` message."""
        if not await mqtt.async_wait_for_mqtt_client(self.hass):
            raise ConfigEntryNotReady("MQTT integration is not connected")

        base = self.base_topic
        self._unsubs.append(await mqtt.async_subscribe(self.hass, f"{base}/bridge/state", self._on_bridge_state, qos=1))
        self._unsubs.append(await mqtt.async_subscribe(self.hass, f"{base}/bridge/info", self._on_bridge_info, qos=1))
        self._unsubs.append(await mqtt.async_subscribe(self.hass, f"{base}/+/state", self._on_circuit_state, qos=0))
        self._unsubs.append(await mqtt.async_subscribe(self.hass, f"{base}/+/program/+", self._on_program, qos=0))
        self._unsubs.append(await mqtt.async_subscribe(self.hass, f"{base}/+/result", self._on_result, qos=1))

        try:
            await asyncio.wait_for(self._info_event.wait(), timeout=MQTT_STARTUP_TIMEOUT)
        except TimeoutError as err:
            self.async_close()
            raise ConfigEntryNotReady(
                f"No weishaupt2mqtt bridge info received on {base}/bridge/info within {MQTT_STARTUP_TIMEOUT:.0f}s"
            ) from err

        self.available = self._bridge_state != "offline"
        self._started_up = True

    def _apply_bridge_info(self, data: dict[str, Any]) -> None:
        self.bridge_info = data
        circuits_list = list(data.get("circuits") or [])
        circuits_set = set(circuits_list)

        addresses: dict[str, BusAddress] = {"31": BusAddress("31", "master", own=True)}
        for dev in self.model.devices.values():
            for c in dev.circuits:
                if c.circuit in circuits_set and c.address != "fe":
                    addresses[c.address.lower()] = BusAddress(
                        c.address.lower(), "slave", manufacturer="Kromschroeder", ident="W",
                        files=(f"weishaupt2mqtt/{c.circuit}",),
                    )
        version = data.get("ebusd_version") or f"weishaupt2mqtt {data.get('bridge_version', '')}".strip()
        self.info = EbusdInfo(version=str(version), signal=bool(data.get("bus_signal", True)), addresses=addresses)
        self.build_capability = str(data.get("run_time_checksum", "unknown"))
        if self.writer is not None:
            self.writer.capability = self.build_capability

        slaves = {a.address for a in addresses.values() if a.role == "slave" and not a.own}
        present = self.model.present_devices(slaves)

        if not self._started_up:
            self.devices = present
            self.unknown_slaves = []
            self.circuits = circuits_set
            self.mismatches = []
            self.scan_incomplete = []
            self.usable = {
                key for key, message in self.model.messages.items()
                if message.circuit in circuits_set and (message.read or message.passive)
            }
            self._info_event.set()
        else:
            new_devices = set(present) - set(self.devices)
            if new_devices and self.entry.state is ConfigEntryState.LOADED:
                _LOGGER.info("MQTT bridge discovered new device(s) %s: reloading entry", ", ".join(sorted(new_devices)))
                self.hass.config_entries.async_schedule_reload(self.entry.entry_id)

    @callback
    def _on_bridge_state(self, msg: mqtt.ReceiveMessage) -> None:
        state = str(msg.payload).strip().lower()
        self._bridge_state = state
        avail = state == "online"
        if self.available != avail:
            self.available = avail
            for update in list(self._availability_listeners):
                update()

    @callback
    def _on_bridge_info(self, msg: mqtt.ReceiveMessage) -> None:
        try:
            data = json.loads(msg.payload)
        except (ValueError, TypeError):
            return
        if isinstance(data, dict):
            self._apply_bridge_info(data)

    @callback
    def _on_circuit_state(self, msg: mqtt.ReceiveMessage) -> None:
        parts = msg.topic.removeprefix(f"{self.base_topic}/").split("/")
        if len(parts) != 2 or parts[1] != "state" or parts[0] == "bridge":
            return
        circuit = parts[0]
        try:
            data = json.loads(msg.payload)
        except (ValueError, TypeError):
            return
        if not isinstance(data, dict):
            return
        for msg_name, val in data.items():
            if msg_name.startswith("_"):
                continue
            key = f"{circuit}/{msg_name}"
            message = self.model.messages.get(key)
            if message is None:
                continue
            self.store(key, _decode_mqtt_message(message, val))

    @callback
    def _on_program(self, msg: mqtt.ReceiveMessage) -> None:
        parts = msg.topic.removeprefix(f"{self.base_topic}/").split("/")
        if len(parts) != 3 or parts[1] != "program":
            return
        circuit, prog_id = parts[0], parts[2]
        group = self.model.groups.get(f"{circuit}/{prog_id}")
        if group is None:
            return
        try:
            data = json.loads(msg.payload)
        except (ValueError, TypeError):
            return
        if not isinstance(data, dict):
            return
        days = data.get("days")
        if not isinstance(days, dict):
            return
        for slot_key in group.members:
            message = self.model.messages.get(slot_key)
            if message is None:
                continue
            pos = message.position or {}
            day = pos.get("day")
            slot_num = pos.get("slot")
            day_ranges = days.get(str(day)) if day is not None else None
            if isinstance(day_ranges, list) and isinstance(slot_num, int) and 1 <= slot_num <= len(day_ranges):
                part = str(day_ranges[slot_num - 1])
                if "-" in part:
                    from_t, to_t = (p.strip() for p in part.split("-", 1))
                    slot_map = {"totime": to_t, "toenabled": "Enabled", "fromtime": from_t, "fromenabled": "Enabled"}
                else:
                    slot_map = {"totime": "00:00", "toenabled": "Disabled", "fromtime": "00:00", "fromenabled": "Disabled"}
            else:
                slot_map = {"totime": "00:00", "toenabled": "Disabled", "fromtime": "00:00", "fromenabled": "Disabled"}
            values = tuple(slot_map.get(f.name, "0" if f.guard else "") for f in message.fields)
            self.store(slot_key, values)

    @callback
    def _on_result(self, msg: mqtt.ReceiveMessage) -> None:
        if not isinstance(self.writer, MqttWriter):
            return
        parts = msg.topic.removeprefix(f"{self.base_topic}/").split("/")
        if len(parts) != 2 or parts[1] != "result":
            return
        try:
            data = json.loads(msg.payload)
        except (ValueError, TypeError):
            return
        if isinstance(data, dict):
            self.writer.handle_result(parts[0], data)

    def async_read_once(self, keys: tuple[str, ...]) -> int:
        """In MQTT mode, the bridge maintains retained state; nothing needs to be queued on TCP."""
        return 0

    async def async_run(self) -> None:
        """Stay active while MQTT subscriptions push live updates."""
        try:
            await self._stop_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            self.async_close()

    @callback
    def async_close(self) -> None:
        self._stop_event.set()
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        super().async_close()


class MqttWriter(Writer):
    """Writer that delegates setting and program writes to `weishaupt2mqtt` over MQTT."""

    def __init__(self, hass: HomeAssistant, hub: MqttHub, options: dict[str, Any]) -> None:
        super().__init__(hass, hub, options)
        self._mqtt_hub = hub
        self._inflight: dict[str, asyncio.Future[dict[str, Any]]] = {}

    async def async_setup(self) -> None:
        self.guard.restore(await self._store.async_load())
        self.specs, self.not_writable = _mqtt_write_specs(self.hub.model, self.hub.circuits, self.hub.usable)
        self.programs, self.slot_specs = _mqtt_program_specs(self.hub.model, self.hub.circuits, self.hub.usable)
        self.clock_writable = False
        self.capability = self.hub.build_capability

    async def async_probe(self) -> str:
        self.capability = self.hub.build_capability
        return self.capability

    def set_switch(self, on: bool) -> None:
        super().set_switch(on)
        payload: dict[str, Any] = {"writes_enabled": on}
        if not on:
            payload["installer_writes_enabled"] = False
        self.hass.async_create_task(
            mqtt.async_publish(
                self.hass,
                f"{self._mqtt_hub.base_topic}/bridge/config/set",
                json.dumps(payload),
                qos=1,
                retain=False,
            )
        )

    @callback
    def handle_result(self, circuit: str, data: dict[str, Any]) -> None:
        cid = data.get("correlation_id")
        if cid and cid in self._inflight:
            fut = self._inflight.pop(cid)
            if not fut.done():
                fut.set_result(data)

    async def _publish_and_wait(self, topic: str, payload: dict[str, Any]) -> dict[str, Any]:
        cid = uuid.uuid4().hex[:12]
        payload = {**payload, "correlation_id": cid}
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._inflight[cid] = fut
        try:
            await mqtt.async_publish(self.hass, topic, json.dumps(payload), qos=1, retain=False)
            return await asyncio.wait_for(fut, timeout=MQTT_WRITE_TIMEOUT)
        except TimeoutError as err:
            self._inflight.pop(cid, None)
            raise WriteFailed("write_failed", setting=topic, reason="bridge timeout") from err
        except Exception:
            self._inflight.pop(cid, None)
            raise

    async def async_write(self, key: str, value: float, user_id: str | None,
                          confirmed: bool = False) -> dict[str, Any]:
        spec = self._check_static(self.specs.get(key), key, value)
        if spec.risk != "comfort" and not confirmed:
            return self._create_pending(spec, value, user_id)  # raises ConfirmationPending

        # Linked bounds check against latest known readings
        low, high = spec.minimum, spec.maximum
        below, above = linked(spec, self.specs)
        for other, is_floor in ((below, True), (above, False)):
            if other is None:
                continue
            vals = self.hub.reading(other.key)
            raw = other.raw_of_values(vals) if vals else None
            if raw is not None:
                bound = other.value_of(raw)
                low, high = (max(low, bound), high) if is_floor else (low, min(high, bound))

        self.guard.check(spec.register_id, value, low, high, None, None)

        # Value to send: ebusd enum name for value lists, numeric value otherwise
        send_val: Any = spec.values[int(value)] if spec.values is not None else value
        if spec.risk == "comfort":
            topic = f"{self._mqtt_hub.base_topic}/{spec.circuit}/set"
            payload: dict[str, Any] = {spec.name: send_val}
        else:
            topic = f"{self._mqtt_hub.base_topic}/{spec.circuit}/installer/set"
            payload = {spec.name: send_val, "confirm": True}

        before_vals = self.hub.reading(key)
        before_raw = spec.raw_of_values(before_vals) if before_vals else None
        before_val = spec.value_of(before_raw) if before_raw is not None else None

        self.guard.record(spec.register_id, None)
        await self._save_guard()

        res = await self._publish_and_wait(topic, payload)
        status = res.get("status", "error")
        entry: dict[str, Any] = {
            "time": time.time(),
            "key": key,
            "register": spec.register_id,
            "source": spec.source,
            "risk": spec.risk,
            "confirmed": confirmed,
            "user_id": user_id,
            "before": res.get("before", before_val),
            "requested": value,
            "telegram": res.get("telegram") or f"mqtt:{topic}",
            "read_back": res.get("read_back"),
            "result": status,
            "frame": f"mqtt:{topic}",
        }
        self._trace(spec, entry)

        if status in ("ok", "unchanged"):
            return entry
        if status in ("refused", "confirmation_required"):
            raise WriteRefused(res.get("reason", "refused"), setting=key, reason=res.get("detail", status))
        if status == "not_taken":
            raise WriteFailed(
                "not_taken",
                setting=key,
                requested=_text(spec, value, self._language()),
                read_back=str(res.get("read_back")),
            )
        raise WriteFailed("write_failed", setting=key, reason=res.get("detail") or status)

    async def async_set_program(self, program_key: str, days: dict[int, str],
                                user_id: str | None) -> dict[str, Any]:
        program = self.programs.get(program_key)
        if program is None:
            raise WriteRefused("not_writable", setting=program_key,
                               reason="the definitions prove no write of this program on this device")
        language = self._language()
        days_payload: dict[str, list[str]] = {}
        for day, text in sorted(days.items()):
            try:
                ranges = parse_day(text)
            except DayError as err:
                raise WriteRefused(f"bad_day_{err.code}", day=DAY_NAMES[language][day - 1], part=err.part) from err
            days_payload[str(day)] = [
                f"{s // 4:02d}:{s % 4 * 15:02d}-{e // 4:02d}:{e % 4 * 15:02d}" for s, e in ranges
            ]

        first = self.slot_specs[program.day_keys(1)[0]]
        self._check_static(first, first.key, 0)

        topic = f"{self._mqtt_hub.base_topic}/{program.circuit}/program/{program.group}/set"
        res = await self._publish_and_wait(topic, {"days": days_payload})
        status = res.get("status", "error")

        now_iso = dt_util.as_local(dt_util.utcnow()).isoformat(timespec="seconds")
        for day, text in days.items():
            self.last_day_writes[(program_key, day)] = {
                "time": now_iso,
                "requested": format_day(parse_day(text)),
                "result": status,
                "slots_written": res.get("slots_written", 0),
            }

        if status in ("ok", "unchanged"):
            return res
        if status == "refused":
            raise WriteRefused(res.get("reason", "refused"), setting=program_key, reason=res.get("detail", status))
        raise WriteFailed("write_failed", setting=program_key, reason=res.get("detail") or status)
