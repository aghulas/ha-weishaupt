"""Base entity: one device per regulator."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WeishauptCoordinator
from .registers import Device


class WeishauptEntity(CoordinatorEntity[WeishauptCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: WeishauptCoordinator, device: Device, key: str, name: str) -> None:
        super().__init__(coordinator)
        self.device = device
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{device.key}_{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.config_entry.entry_id}_{device.key}")},
            name=device.name, manufacturer="Weishaupt", model=f"eBUS {device.zz}")

    def raw(self, register: str) -> bytes | None:
        return (self.coordinator.data or {}).get(self.device.key, {}).get(register)
