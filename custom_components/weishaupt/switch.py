"""The write switch: writes are refused while it is off. Created only when writes are enabled in the options of
the entry, off at first, then as it was left."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_ON, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .entity import hub_identifier
from .hub import Hub, WeishauptConfigEntry

PARALLEL_UPDATES = 0


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    hub = entry.runtime_data
    if hub.writer is not None:
        async_add_entities([WriteSwitch(hub)])


class WriteSwitch(SwitchEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = "writes"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hub: Hub) -> None:
        self.hub = hub
        self._attr_unique_id = f"{hub.entry.entry_id}_writes"
        self._attr_device_info = DeviceInfo(identifiers={hub_identifier(hub)})

    async def async_added_to_hass(self) -> None:
        last = await self.async_get_last_state()
        self.hub.writer.set_switch(last is not None and last.state == STATE_ON)

    @property
    def is_on(self) -> bool:
        return self.hub.writer.switch_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        writer = self.hub.writer
        return {"run_time_checksum": writer.capability, "writable_settings": len(writer.specs),
                "writes_last_hour": writer.guard.writes_last_hour()}

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.hub.writer.set_switch(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.hub.writer.set_switch(False)
        self.hub.writer.drop_all_pending()
        self.async_write_ha_state()
