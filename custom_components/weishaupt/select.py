"""The settings the definitions prove writable that take an entry of a value list (legionella day, circulation
during legionella protection, holiday temperature level), as select entities. Created only when writes are enabled
in the options; every change goes through the writer and its guard, with the confirmation of its risk class, as
the numbers (`number.py`). Options are the keys of the ebusd names, labelled in the translations."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .hub import Hub, WeishauptConfigEntry
from .model import NumberDescription
from .number import SettingEntity
from .writes import WriteSpec

PARALLEL_UPDATES = 1  # one write at a time


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    hub = entry.runtime_data
    if hub.writer is None:
        return
    async_add_entities(
        SettingSelect(hub, description, hub.writer.specs[description.message.key])
        for description in hub.model.select_entities
        if description.message.key in hub.writer.specs
        and hub.named("select", description.translation_key, description.message.device, description.name))


class SettingSelect(SettingEntity, SelectEntity):
    def __init__(self, hub: Hub, description: NumberDescription, spec: WriteSpec) -> None:
        super().__init__(hub, description, spec)
        self._raw = {key: int(raw) for key, raw in description.options.items()}  # option key -> register value
        self._key_of = {name: key for key, name in
                        ((k, spec.values[r]) for k, r in self._raw.items())}  # ebusd name -> option key
        self._attr_options = list(self._raw)

    @property
    def current_option(self) -> str | None:
        values = self.hub.reading(self._spec.key)
        return self._key_of.get(values[0]) if values else None

    async def async_select_option(self, option: str) -> None:
        await self._async_write(self._raw[option])
