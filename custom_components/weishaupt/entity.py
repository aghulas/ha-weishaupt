"""Base entity: one Home Assistant device per controller on the bus, attached to the ebusd hub device."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, MANUFACTURER, MODELS
from .hub import Hub
from .model import Device

TEXT_TYPES = ("HEX", "STR", "NTS", "TTM", "TTH", "TTQ", "BTI", "HTI", "VTI", "BTM", "HTM", "VTM", "BDA", "HDA", "BDZ")
NOT_AVAILABLE = "-"  # what ebusd answers for the replacement value of a type



def hub_identifier(hub: Hub) -> tuple[str, str]:
    return (DOMAIN, hub.entry.entry_id)


def device_identifier(hub: Hub, device: Device) -> tuple[str, str]:
    return (DOMAIN, f"{hub.entry.entry_id}_{device.id}")


def _version(raw: str | None) -> str | None:
    """`1104` of the scan -> `11.04`."""
    if not raw or raw == NOT_AVAILABLE:
        return None
    return f"{raw[:2]}.{raw[2:]}" if len(raw) == 4 and raw.isdigit() else raw


def parse_number(text: str | None) -> int | float | None:
    if text is None or text == NOT_AVAILABLE:
        return None
    try:
        return float(text) if "." in text else int(text)
    except ValueError:
        return None


class WeishauptEntity(Entity):
    """An entity fed by the readings of one or several messages."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _read_priority: int | None = None  # class of its messages in the reader (hub.SETTING_PRIORITY for settings)

    def __init__(self, hub: Hub, device: Device, key: str, translation_key: str, messages: tuple[str, ...]) -> None:
        self.hub = hub
        self._messages = messages
        self._attr_unique_id = f"{hub.entry.entry_id}_{key}"
        self._attr_translation_key = translation_key
        scan = hub.address_of(device)
        self._attr_device_info = DeviceInfo(
            identifiers={device_identifier(hub, device)},
            translation_key=device.id,
            manufacturer=MANUFACTURER,
            model=MODELS.get(device.type),
            sw_version=_version(scan.software) if scan else None,
            hw_version=_version(scan.hardware) if scan else None,
            via_device_id=hub.device_id,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.hub.async_listen(self._messages, self.async_write_ha_state, self._read_priority))

    @property
    def available(self) -> bool:
        return self.hub.available
