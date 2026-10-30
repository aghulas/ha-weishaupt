"""Settings with named values (e.g. holiday temperature level of the FS) as select entities."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WeishauptConfigEntry, WeishauptCoordinator
from .entity import WeishauptEntity
from .protocol import UNIT
from .registers import DEVICES, Choice, Device, choices_of


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(WeishauptSelect(coordinator, device, choice)
                       for device in DEVICES for choice in choices_of(device))


class WeishauptSelect(WeishauptEntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: WeishauptCoordinator, device: Device, choice: Choice) -> None:
        super().__init__(coordinator, device, choice.key, choice.name)
        self.choice = choice
        self._attr_options = list(choice.options.values())

    @property
    def current_option(self) -> str | None:
        raw = self.raw(self.choice.register)
        return None if raw is None else self.choice.options.get(int(UNIT.decode(raw)))

    async def async_select_option(self, option: str) -> None:
        """ÉCRITURE: through the guard of the coordinator."""
        value = next(k for k, v in self.choice.options.items() if v == option)
        keys = list(self.choice.options)
        await self.coordinator.async_write(self.device, self.choice.register, UNIT.encode(value), value,
                                           min(keys), max(keys), self.choice.source)
