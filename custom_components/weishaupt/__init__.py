"""Weishaupt WCM regulators through ebusd (registers read with 5022, written with 5023 and the Weishaupt CRC)."""
from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .coordinator import WeishauptConfigEntry, WeishauptCoordinator
from .protocol import EbusdClient

PLATFORMS = [Platform.DATE, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry) -> bool:
    client = EbusdClient(entry.data[CONF_HOST], entry.data[CONF_PORT])
    coordinator = WeishauptCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WeishauptConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: WeishauptConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
