"""Sensors built from the metadata: values, enumerations, weekly programs, fault history. Read-only."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change, async_track_time_interval
from homeassistant.util import dt as dt_util

from . import clock
from .ebusd import EbusdError
from .entity import NOT_AVAILABLE, TEXT_TYPES, WeishauptEntity, parse_number
from .hub import Hub, WeishauptConfigEntry
from .model import WEEKDAYS, GroupEntity, ValueEntity

PARALLEL_UPDATES = 0  # the entities never ask: the hub reads, one request at a time

UNITS = {
    "°C": (UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    "K": (UnitOfTemperature.KELVIN, SensorDeviceClass.TEMPERATURE_DELTA),
    "%": (PERCENTAGE, None),
    "h": (UnitOfTime.HOURS, SensorDeviceClass.DURATION),
    "min": (UnitOfTime.MINUTES, SensorDeviceClass.DURATION),
    "s": (UnitOfTime.SECONDS, SensorDeviceClass.DURATION),
}
# Address arithmetic of the fault history of the boiler automat, from the evidence record `bc-fault-history` of
# the definitions: the pointer is the address of the last byte written; slot n is the 8 bytes ending at
# 0x0201 + 8 n. The metadata does not carry it yet.
FAULT_SLOT_BASE, FAULT_SLOT_SIZE = 0x0201, 8


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    hub = entry.runtime_data
    entities: list[SensorEntity] = [
        ValueSensor(hub, description) for description in hub.model.value_entities
        if description.platform == "sensor" and description.message.key in hub.usable
        and hub.named("sensor", description.translation_key, description.message.device)]
    for description in hub.model.group_entities:
        if not all(member in hub.usable for member in description.group.members) or not hub.named(
                "sensor", description.translation_key, description.group.device):
            continue
        if description.group.family == "program":
            entities.append(ProgramSensor(hub, description))
        elif description.group.family == "fault_history":
            entities.append(FaultHistorySensor(hub, description))
    system = next((d for d in hub.devices.values() if d.type == "system"), None)
    if system is not None and hub.usable:
        entities.append(ClockOffsetSensor(hub, system))
    async_add_entities(entities)


class ValueSensor(WeishauptEntity, SensorEntity):
    """One field of one message."""

    def __init__(self, hub: Hub, description: ValueEntity) -> None:
        message, fld = description.message, description.field
        super().__init__(hub, hub.model.device_of(message), description.key, description.translation_key,
                         (message.key,))
        self._key, self._index = message.key, fld.index
        self._options = description.options
        self._text = fld.type.startswith(TEXT_TYPES)
        self._attr_entity_registry_enabled_default = description.enabled_default
        if description.diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if self._options is not None:
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = list(dict.fromkeys(self._options.values()))
        elif not self._text:
            unit, device_class = UNITS.get(fld.unit or "", (fld.unit, None))
            self._attr_native_unit_of_measurement = unit
            self._attr_device_class = device_class
            if description.kind == "counter":
                self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            elif description.kind == "live":
                self._attr_state_class = SensorStateClass.MEASUREMENT
            if fld.divisor is not None and fld.divisor > 1:
                self._attr_suggested_display_precision = len(str(fld.divisor)) - 1
            elif fld.type in ("D2B", "D2C"):
                self._attr_suggested_display_precision = 1

    @property
    def native_value(self) -> int | float | str | None:
        values = self.hub.reading(self._key)
        if values is None:
            return None
        text = values[self._index]
        if self._options is not None:
            return self._options.get(text)
        if self._text:
            return None if text == NOT_AVAILABLE else text
        return parse_number(text)


class GroupSensor(WeishauptEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hub: Hub, description: GroupEntity, extra: tuple[str, ...] = ()) -> None:
        group = description.group
        super().__init__(hub, hub.model.devices[group.device], description.key, description.translation_key,
                         group.members + extra)
        self._group = group
        self._attr_entity_registry_enabled_default = description.enabled_default

    def _fields(self, key: str) -> dict[str, str] | None:
        """Field name -> text of the last reading of a member."""
        values = self.hub.reading(key)
        if values is None:
            return None
        return {fld.name: values[fld.index] for fld in self.hub.model.messages[key].fields}


class ProgramSensor(GroupSensor):
    """A weekly program: state = the switch times of today, one attribute per day (`06:30-18:00, 19:00-21:00`)."""

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # the state is "today": write it again when the day changes
        self.async_on_remove(async_track_time_change(
            self.hass, lambda _now: self.schedule_update_ha_state(), hour=0, minute=0, second=10))

    def _day(self, day: int) -> str | None:
        slots = []
        for key in self._group.members:
            message = self.hub.model.messages[key]
            if (message.position or {}).get("day") != day:
                continue
            fields = self._fields(key)
            if fields is None:
                return None
            if fields.get("fromenabled") == "Enabled" and fields.get("toenabled") == "Enabled":
                slots.append((message.position["slot"], f"{fields['fromtime']}-{fields['totime']}"))
        return ", ".join(text for _, text in sorted(slots)) or "-"

    @property
    def native_value(self) -> str | None:
        return self._day(dt_util.now().isoweekday())

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {name: text for day, name in enumerate(WEEKDAYS, 1) if (text := self._day(day)) is not None}


class FaultHistorySensor(GroupSensor):
    """Fault memory of a boiler: state = the most recent entry (`W12`, `F11`), attribute `entries` = all of them,
    most recent first, each with the values the automat stored with it."""

    def __init__(self, hub: Hub, description: GroupEntity) -> None:
        pointer = f"{description.group.circuit}/FaultHistoryPointer"
        self._pointer = pointer if pointer in hub.usable else None
        super().__init__(hub, description, (pointer,) if self._pointer else ())

    def _entries(self) -> list[dict[str, Any]] | None:
        slots = []
        for key in self._group.members:
            fields = self._fields(key)
            if fields is None:
                return None
            message = self.hub.model.messages[key]
            number = parse_number(fields.get("number"))
            entry: dict[str, Any] = {"slot": (message.position or {}).get("n")}
            if number:  # an empty slot reads 0
                entry["code"] = f"{'W' if fields.get('kind') == 'warning' else 'F'}{number}"
                for fld in message.fields:
                    if fld.shown and fld.name not in ("number", "kind"):
                        text = fields[fld.name]
                        entry[fld.name] = text if fld.values else parse_number(text)
            slots.append(entry)
        newest = None
        if self._pointer and (pointer := self._fields(self._pointer)) is not None:
            position = parse_number(pointer.get("value"))
            if isinstance(position, int) and (position - FAULT_SLOT_BASE) % FAULT_SLOT_SIZE == 0:
                newest = (position - FAULT_SLOT_BASE) // FAULT_SLOT_SIZE
        if newest is not None and 1 <= newest <= len(slots):
            slots = [slots[(newest - 1 - i) % len(slots)] for i in range(len(slots))]
        return [entry for entry in slots if "code" in entry]

    @property
    def native_value(self) -> str | None:
        entries = self._entries()
        if entries is None:
            return None
        return entries[0]["code"] if entries else "-"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        entries = self._entries()
        return {} if entries is None else {"entries": entries, "ordered": self._ordered()}

    def _ordered(self) -> bool:
        """True when the pointer was read, so that the first entry is the most recent one."""
        return bool(self._pointer and self.hub.reading(self._pointer) is not None)


class ClockOffsetSensor(WeishauptEntity, SensorEntity):
    """Seconds the clock master of the installation is ahead of the clock of ebusd's host (negative: behind), from
    its last date and time broadcast, which ebusd keeps in its cache: no request to the bus. Read every minute.
    Unknown when the last broadcast came from ebusd itself, or when ebusd's host does not agree with Home Assistant
    on the time within two minutes (`clock.offset`)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, hub: Hub, device) -> None:
        super().__init__(hub, device, "broadcast/Datetime/offset", "clock_offset", ())
        self._value: float | None = None
        self._broadcast: clock.Broadcast | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(async_track_time_interval(self.hass, self._async_update, timedelta(seconds=60)))
        await self._async_update()

    async def _async_update(self, _now=None) -> None:
        try:
            broadcast = clock.parse_find(await self.hub.client.last_broadcast_of_clock())
        except EbusdError:
            broadcast = None
        if broadcast is not None and broadcast.source == self.hub.own_address:
            return  # ebusd's own broadcast carries what was sent: keep the master's last figure
        self._broadcast = broadcast
        self._value = None if broadcast is None else clock.offset(
            broadcast, self.hub.own_address, dt_util.now().replace(tzinfo=None))
        if self.hub.writer is not None and broadcast is not None:
            self.hub.writer.last_clock = broadcast
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        return self._value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        b = self._broadcast
        return {} if b is None else {"master": b.source, "carried": b.carried.isoformat(),
                                     "received": b.received.isoformat()}
