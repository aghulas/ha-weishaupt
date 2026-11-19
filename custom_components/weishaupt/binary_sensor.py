"""Binary sensors: the on/off states of the metadata (flame, pump, fault…). Read-only."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import WeishauptEntity
from .hub import Hub, WeishauptConfigEntry
from .model import ValueEntity

PARALLEL_UPDATES = 0  # the entities never ask: the hub reads, one request at a time


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    hub = entry.runtime_data
    async_add_entities(
        ValueBinarySensor(hub, description) for description in hub.model.value_entities
        if description.platform == "binary_sensor" and description.message.key in hub.usable
        and hub.named("binary_sensor", description.translation_key, description.message.device,
                      description.name))


class ValueBinarySensor(WeishauptEntity, BinarySensorEntity):
    def __init__(self, hub: Hub, description: ValueEntity) -> None:
        message = description.message
        super().__init__(hub, hub.model.device_of(message), description.key, description.translation_key,
                         (message.key,), description.name)
        self._key, self._index = message.key, description.field.index
        self._attr_entity_registry_enabled_default = description.enabled_default
        if description.diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool | None:
        values = self.hub.reading(self._key)
        if values is None or values[self._index] not in ("on", "off"):
            return None
        return values[self._index] == "on"
