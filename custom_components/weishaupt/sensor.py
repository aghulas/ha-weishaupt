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
from .registers import DAYS, DEVICES, PROGRAMS, Device, Program


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(WeishauptProgram(coordinator, device, program) for device in DEVICES for program in PROGRAMS)


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
