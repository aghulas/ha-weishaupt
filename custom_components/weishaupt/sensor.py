"""Time programs as sensors: state = today's slots, one attribute per day."""
from __future__ import annotations

import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import WeishauptConfigEntry, WeishauptCoordinator
from .entity import WeishauptEntity
from .protocol import decode_slot, format_slots
from .registers import DAYS, DEVICES, PROGRAMS, Device, Program, ReadParam, polls_programs, read_params_of


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    entities: list[WeishauptEntity] = [WeishauptProgram(coordinator, device, program)
                                       for device in DEVICES if polls_programs(device) for program in PROGRAMS]
    entities += [WeishauptReadParam(coordinator, device, param)
                 for device in DEVICES for param in read_params_of(device)]
    async_add_entities(entities)


class WeishauptProgram(WeishauptEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: WeishauptCoordinator, device: Device, program: Program) -> None:
        super().__init__(coordinator, device, f"program_{program.key}", program.name)
        self.program = program

    def slots(self, day: int) -> list[tuple[int, int] | None] | None:
        raws = [self.raw(self.program.register(day, s)) for s in range(1, 4)]
        if any(r is None for r in raws):
            return None
        return [decode_slot(r) for r in raws]

    @property
    def available(self) -> bool:
        return super().available and self.slots(1) is not None

    @property
    def native_value(self) -> str | None:
        slots = self.slots(dt_util.now().isoweekday())
        return None if slots is None else format_slots(slots)

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {name: format_slots(slots) for day, name in enumerate(DAYS, 1) if (slots := self.slots(day)) is not None}


class WeishauptReadParam(WeishauptEntity, SensorEntity):
    """A regulation register exposed READ-ONLY (anticipation / régulation fine) ahead of its write validation."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: WeishauptCoordinator, device: Device, param: ReadParam) -> None:
        super().__init__(coordinator, device, f"read_{param.key}", param.name)
        self.param = param
        self._attr_native_unit_of_measurement = None if param.options else param.unit

    @property
    def available(self) -> bool:
        return super().available and self.raw(self.param.register) is not None

    @property
    def native_value(self) -> float | str | None:
        raw = self.raw(self.param.register)
        if raw is None:
            return None
        value = self.param.codec.decode(raw)
        if self.param.options is not None:
            return self.param.options.get(int(value), str(int(value)))
        return value
