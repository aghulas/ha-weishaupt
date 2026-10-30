"""Weishaupt WCM regulators through ebusd (registers read with 5022, written with 5023 and the Weishaupt CRC)."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.const import ATTR_ENTITY_ID, CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_registry as er

from .const import DOMAIN
from .coordinator import WeishauptConfigEntry, WeishauptCoordinator
from .protocol import EbusdClient, encode_slot, parse_slots
from .registers import DAYS, DEVICES, PROGRAM_SOURCE, PROGRAMS

PLATFORMS = [Platform.DATE, Platform.NUMBER, Platform.SENSOR]
SET_TIME_PROGRAM_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_id,
    vol.Required("day"): vol.In(DAYS),
    vol.Required("slots"): cv.string,
})


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry) -> bool:
    client = EbusdClient(entry.data[CONF_HOST], entry.data[CONF_PORT])
    coordinator = WeishauptCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if not hass.services.has_service(DOMAIN, "set_time_program"):
        hass.services.async_register(DOMAIN, "set_time_program", _time_program_handler(hass), SET_TIME_PROGRAM_SCHEMA)
    return True


def _time_program_handler(hass: HomeAssistant):
    async def set_time_program(call: ServiceCall) -> None:
        """ÉCRITURE: the 3 slots of one day of a time program (unused slots cleared), one register per write,
        unchanged slots not rewritten."""
        entry_ = er.async_get(hass).async_get(call.data[ATTR_ENTITY_ID])
        if entry_ is None or entry_.platform != DOMAIN or "_program_" not in entry_.unique_id:
            raise ServiceValidationError("choisir un capteur de programme horaire Weishaupt")
        config_entry = hass.config_entries.async_get_entry(entry_.config_entry_id)
        coordinator: WeishauptCoordinator = config_entry.runtime_data
        suffix = entry_.unique_id.removeprefix(f"{config_entry.entry_id}_")
        device = next(d for d in DEVICES if suffix.startswith(f"{d.key}_program_"))
        program = next(p for p in PROGRAMS if suffix == f"{device.key}_program_{p.key}")
        try:
            slots = parse_slots(call.data["slots"])
        except ValueError as err:
            raise ServiceValidationError(f"créneaux invalides : {err}") from err
        day = DAYS.index(call.data["day"]) + 1
        for number in range(1, 4):
            slot = slots[number - 1] if number <= len(slots) else None
            raw = encode_slot(slot)
            register = program.register(day, number)
            if (coordinator.data or {}).get(device.key, {}).get(register) == raw:
                continue
            await coordinator.async_write(device, register, raw, raw[0], 0, 0x80, PROGRAM_SOURCE)

    return set_time_program


async def async_unload_entry(hass: HomeAssistant, entry: WeishauptConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: WeishauptConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
