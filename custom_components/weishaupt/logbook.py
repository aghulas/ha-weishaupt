"""Logbook entries for the changes written to the heating system: one per change asked by a user (a setting, a
program day, the clock), on its entity, with before -> after, the frames sent and the result of the read-back. The
logbook needs no setting, unlike the info lines of the log (Home Assistant logs warnings and above by default)."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.logbook import LOGBOOK_ENTRY_ENTITY_ID, LOGBOOK_ENTRY_MESSAGE, LOGBOOK_ENTRY_NAME
from homeassistant.core import Event, HomeAssistant, callback

from .const import DOMAIN, EVENT_CHANGE


@callback
def async_describe_events(hass: HomeAssistant,
                          async_describe_event: Callable[[str, str, Callable[[Event], dict[str, Any]]], None]) -> None:
    @callback
    def describe(event: Event) -> dict[str, Any]:
        entity_id = event.data.get("entity_id")
        state = hass.states.get(entity_id) if entity_id else None
        described = {LOGBOOK_ENTRY_NAME: state.name if state else "Weishaupt",
                     LOGBOOK_ENTRY_MESSAGE: event.data["message"]}
        if entity_id:
            described[LOGBOOK_ENTRY_ENTITY_ID] = entity_id
        return described

    async_describe_event(DOMAIN, EVENT_CHANGE, describe)
