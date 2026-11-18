"""The settings the definitions prove writable, as number entities. Created only when writes are enabled in the
options of the entry; every change goes through the writer and its guard (`writer.py`).

A comfort setting is written when it is set. A regulation setting is not: setting it opens a confirmation in
Settings > Repairs, which shows the current value, the new value and the range, and writes only once confirmed."""
from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .entity import WeishauptEntity, parse_number
from .guard import WriteRefused
from .hub import Hub, WeishauptConfigEntry
from .model import NumberDescription
from .sensor import UNITS
from .writer import ConfirmationPending, WriteFailed
from .writes import WriteSpec

PARALLEL_UPDATES = 1  # one write at a time


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    hub = entry.runtime_data
    if hub.writer is None:
        return
    async_add_entities(
        SettingNumber(hub, description, hub.writer.specs[description.message.key])
        for description in hub.model.number_entities
        if description.message.key in hub.writer.specs)


class SettingNumber(WeishauptEntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX

    def __init__(self, hub: Hub, description: NumberDescription, spec: WriteSpec) -> None:
        message = description.message
        super().__init__(hub, hub.model.device_of(message), description.key, description.translation_key,
                         (message.key,))
        self._spec = spec
        self._attr_native_min_value = spec.minimum
        self._attr_native_max_value = spec.maximum
        self._attr_native_step = spec.step
        unit, device_class = UNITS.get(spec.unit or "", (spec.unit, None))
        self._attr_native_unit_of_measurement = unit
        # regulation settings are created disabled: they are not for a dashboard
        self._attr_entity_registry_enabled_default = spec.risk == "comfort"

    @property
    def native_value(self) -> float | None:
        values = self.hub.reading(self._spec.key)
        number = parse_number(values[0]) if values else None
        return None if number is None else float(number)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        spec = self._spec
        return {"risk": spec.risk, "proof": spec.proof, "open_questions": list(spec.open),
                "source": spec.source, "bounds_from": spec.bounds_from}

    async def async_set_native_value(self, value: float) -> None:
        writer = self.hub.writer
        user_id = self._context.user_id if self._context else None
        try:
            await writer.async_request(self._spec.key, value, user_id)
        except ConfirmationPending as pending:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="confirmation_pending",
                                         translation_placeholders=pending.placeholders) from None
        except WriteRefused as err:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key=err.code,
                                         translation_placeholders=err.placeholders) from err
        except WriteFailed as err:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key=err.code,
                                     translation_placeholders=err.placeholders) from err
        finally:
            self.async_write_ha_state()
