"""The action `weishaupt.set_program`: write the days of a weekly program at once.

For an automation or to copy a week: comfort class, so no confirmation, like the text entities of the days. Only
the slots that change are written, three at most a day, so 21 writes at most for a whole week. Every day given is
checked first, then the slots are read from the device; when the slots to write are more than the writes left
within the hour (the option *Maximum writes per hour*, 30 by default), nothing is written and the action fails
with the count. A failure in the middle stops the rest and says how many were written.
"""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr

from .const import DOMAIN
from .guard import WriteRefused
from .model import WEEKDAYS
from .writer import WriteFailed

SET_PROGRAM = "set_program"
SCHEMA = vol.Schema({
    vol.Required("device_id"): cv.string,
    vol.Required("program"): cv.string,
    **{vol.Optional(day): cv.string for day in WEEKDAYS},
})


@callback
def async_register_services(hass: HomeAssistant) -> None:
    hass.services.async_register(DOMAIN, SET_PROGRAM, _async_set_program, schema=SCHEMA,
                                 supports_response=SupportsResponse.OPTIONAL)


async def _async_set_program(call: ServiceCall) -> ServiceResponse:
    hass = call.hass
    device = dr.async_get(hass).async_get(call.data["device_id"])
    if device is None:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="unknown_device")
    for entry_id in device.config_entries:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != DOMAIN or entry.state is not ConfigEntryState.LOADED:
            continue
        hub = entry.runtime_data
        if hub.writer is None:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="writes_disabled")
        circuit = next((p.circuit for p in hub.writer.programs.values()
                        if any(f"{entry.entry_id}_{p.device}" == ident for _, ident in device.identifiers)), None)
        shared = next((hub.model.shared_group(g) for g in hub.model.groups.values()
                       if g.family == "program" and g.id == call.data["program"]
                       and any(f"{entry.entry_id}_{g.device}" == ident for _, ident in device.identifiers)), None)
        if shared is not None:
            # this device reads the program from another one's store: a write here would be acknowledged and lost
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="program_shared",
                                         translation_placeholders={
                                             "program": hub.label(shared.label),
                                             "device": hub.label(hub.model.devices[shared.device].label)})
        if circuit is None:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_writable",
                                         translation_placeholders={"setting": call.data["program"],
                                                                   "reason": "no writable program on this device"})
        days = {number: call.data[day] for number, day in enumerate(WEEKDAYS, 1) if day in call.data}
        try:
            result = await hub.writer.async_set_program(f"{circuit}/{call.data['program']}", days,
                                                        call.context.user_id)
        except WriteRefused as err:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key=err.code,
                                         translation_placeholders=err.placeholders) from err
        except WriteFailed as err:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key=err.code,
                                     translation_placeholders=err.placeholders) from err
        return result if call.return_response else None
    raise ServiceValidationError(translation_domain=DOMAIN, translation_key="unknown_device")
