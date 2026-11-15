"""Master write switch (coupe-circuit) for the Weishaupt integration.

One switch that enables or disables EVERY write to the boiler regulators at runtime: the write guard
(guard.WriteGuard.check / check_broadcast) refuses every write while it is off. It is off by default and after any
restart (fail-safe); the agent writes only while it is on, and a single click stops everything. It stays operable
even when polling fails, so writes can always be cut.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WeishauptConfigEntry, WeishauptCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities([WeishauptWriteSwitch(entry.runtime_data)])


class WeishauptWriteSwitch(CoordinatorEntity[WeishauptCoordinator], SwitchEntity):
    """Interrupteur global des écritures (coupe-circuit). État = coordinator.guard.enabled."""

    _attr_has_entity_name = True
    _attr_name = "Écritures agent chaudière"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:shield-key"

    def __init__(self, coordinator: WeishauptCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_writes_enabled"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.config_entry.entry_id}_agent")},
            name="Weishaupt — agent", manufacturer="Weishaupt", model="Garde-fou écritures")

    @property
    def available(self) -> bool:
        """Always operable: a kill switch must work even if a poll failed."""
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.guard.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """ÉCRITURE (activation): autorise les écritures (le garde-fou reste appliqué à chaque write)."""
        self.coordinator.guard.enabled = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Coupe toutes les écritures immédiatement."""
        self.coordinator.guard.enabled = False
        self.async_write_ha_state()
