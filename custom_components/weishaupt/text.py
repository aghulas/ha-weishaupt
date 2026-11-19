"""Weekly programs that the definitions prove writable, as one text entity per program and day:
`06:30-18:00, 19:00-21:00`, up to three ranges in quarters of an hour, `-` for none (`programs.py`). Created only
when writes are enabled, and only for the programs whose slots have write conditions on that device (room unit 1,
heating program 1 of room unit 3; never room unit 2). Heating program 1 is enabled when created, the others not.
Comfort class: setting a day writes its three slots at once, through the guard, and reads them back.

The entity has no pattern: Home Assistant would refuse a text that does not match it with its own message, the raw
regular expression. Every text reaches the integration, which checks the shape, the quarters of an hour, the order
and the overlap, and refuses with a translated message that shows the expected format. The last write
of the day is in the attribute `last_write`: time, before -> after, the frames, the result of the read-back."""
from __future__ import annotations

from typing import Any

from homeassistant.components.text import TextEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .entity import WeishauptEntity
from .guard import WriteRefused
from .hub import SETTING_PRIORITY, Hub, WeishauptConfigEntry
from .model import WEEKDAYS
from .programs import MAX_LENGTH, Program
from .writer import WriteFailed

PARALLEL_UPDATES = 1
ENABLED_PROGRAM = "heating1"


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    hub = entry.runtime_data
    if hub.writer is None:
        return
    async_add_entities(ProgramDayText(hub, program, day)
                       for program in hub.writer.programs.values() for day in range(1, 8)
                       if hub.named("text", f"program_{program.group}_{WEEKDAYS[day - 1]}", program.device))


class ProgramDayText(WeishauptEntity, TextEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_max = MAX_LENGTH
    # its three slots are read right after the numbers and selects (within that class the 24-hour interval of the
    # programs comes after the 6 hours of the settings), not after the whole first pass
    _read_priority = SETTING_PRIORITY

    def __init__(self, hub: Hub, program: Program, day: int) -> None:
        name = WEEKDAYS[day - 1]
        super().__init__(hub, hub.model.devices[program.device], f"{program.key}/{name}",
                         f"program_{program.group}_{name}", program.day_keys(day))
        self._program, self._day = program, day
        self._attr_entity_registry_enabled_default = program.group == ENABLED_PROGRAM

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.hub.writer.entity_ids[(self._program.key, self._day)] = self.entity_id

    @property
    def native_value(self) -> str | None:
        """The day once its three slots are read; unknown until then (a day of one or two slots could be wrong)."""
        return self.hub.writer.program_day(self._program, self._day)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        spec = self.hub.writer.slot_specs[self._program.day_keys(self._day)[0]]
        return {"risk": spec.risk, "proof": spec.proof, "source": spec.source,
                "registers": [self.hub.writer.slot_specs[k].register for k in self._program.day_keys(self._day)],
                "last_write": self.hub.writer.last_day_writes.get((self._program.key, self._day))}

    async def async_set_value(self, value: str) -> None:
        user_id = self._context.user_id if self._context else None
        try:
            await self.hub.writer.async_write_day(self._program.key, self._day, value, user_id)
        except WriteRefused as err:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key=err.code,
                                         translation_placeholders=err.placeholders) from err
        except WriteFailed as err:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key=err.code,
                                     translation_placeholders=err.placeholders) from err
        finally:
            self.async_write_ha_state()
