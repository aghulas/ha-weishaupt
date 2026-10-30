"""Holiday dates of the FS as date entities (three registers each: day, month, 2-digit year)."""
from __future__ import annotations

import datetime

from homeassistant.components.date import DateEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WeishauptConfigEntry, WeishauptCoordinator
from .entity import WeishauptEntity
from .protocol import UNIT
from .registers import DEVICES, DateSetting, Device, dates_of

# guard bounds of each part (day, month, year)
PART_BOUNDS = ((1, 31), (1, 12), (0, 99))


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(WeishauptDate(coordinator, device, setting)
                       for device in DEVICES for setting in dates_of(device))


class WeishauptDate(WeishauptEntity, DateEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: WeishauptCoordinator, device: Device, setting: DateSetting) -> None:
        super().__init__(coordinator, device, setting.key, setting.name)
        self.setting = setting

    @property
    def native_value(self) -> datetime.date | None:
        parts = [self.raw(r) for r in self.setting.registers]
        if any(p is None for p in parts):
            return None
        day, month, year = (int(UNIT.decode(p)) for p in parts)
        try:
            return datetime.date(2000 + year, month, day)
        except ValueError:
            return None  # e.g. the values found before the first holiday was set (03/09/01)

    async def async_set_value(self, value: datetime.date) -> None:
        """ÉCRITURE: day, month and year, one register per write, through the guard of the coordinator."""
        if not 2000 <= value.year <= 2099:
            raise HomeAssistantError("année hors de 2000-2099")
        for register, part, (low, high) in zip(self.setting.registers, (value.day, value.month, value.year - 2000),
                                               PART_BOUNDS, strict=True):
            await self.coordinator.async_write(self.device, register, UNIT.encode(part), part, low, high,
                                               self.setting.source)
