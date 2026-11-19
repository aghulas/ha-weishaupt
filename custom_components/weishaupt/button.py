"""The set-clock button, on the device of the installation: created only when writes are enabled and the
definitions prove the date and time broadcast. Regulation class: pressing it sends nothing and asks for a
confirmation in Settings > Repairs; the confirmed broadcast goes out at second 00 of the next minute, or not at all
(`writer.async_set_clock`). There is no action: no automation sets the clock."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .entity import WeishauptEntity
from .guard import WriteRefused
from .hub import Hub, WeishauptConfigEntry
from .writer import CLOCK_KEY, ConfirmationPending

PARALLEL_UPDATES = 1


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    hub = entry.runtime_data
    if hub.writer is None or not hub.writer.clock_writable:
        return
    device = hub.model.devices[hub.model.messages[CLOCK_KEY].device]
    if device.id in hub.devices:
        async_add_entities([SetClockButton(hub, device)])


class SetClockButton(WeishauptEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hub: Hub, device) -> None:
        super().__init__(hub, device, "broadcast/Datetime/set", "set_clock", ())

    async def async_press(self) -> None:
        user_id = self._context.user_id if self._context else None
        try:
            await self.hub.writer.async_request_clock(user_id)
        except ConfirmationPending:
            pass  # not an error: the repair and a notification ask for the confirmation
        except WriteRefused as err:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key=err.code,
                                         translation_placeholders=err.placeholders) from err
