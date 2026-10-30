"""Settings of the regulators as number entities."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WeishauptConfigEntry, WeishauptCoordinator
from .entity import WeishauptEntity
from .registers import DEVICES, Device, Setting, settings_of


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(WeishauptNumber(coordinator, device, setting)
                       for device in DEVICES for setting in settings_of(device))


class WeishauptNumber(WeishauptEntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: WeishauptCoordinator, device: Device, setting: Setting) -> None:
        super().__init__(coordinator, device, setting.key, setting.name)
        self.setting = setting
        self._attr_native_min_value = setting.minimum
        self._attr_native_max_value = setting.maximum
        self._attr_native_step = setting.step
        self._attr_native_unit_of_measurement = setting.unit

    @property
    def available(self) -> bool:
        return super().available and self.raw(self.setting.register) is not None

    @property
    def native_value(self) -> float | None:
        raw = self.raw(self.setting.register)
        return None if raw is None else self.setting.codec.decode(raw)

    async def async_set_native_value(self, value: float) -> None:
        """ÉCRITURE: through the guard of the coordinator."""
        s = self.setting
        await self.coordinator.async_write(self.device, s.register, s.codec.encode(value), value,
                                           s.minimum, s.maximum, s.source)
