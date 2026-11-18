"""Confirmation of a change of a regulation setting.

Setting a regulation setting creates a fixable repair issue; its flow shows the setting, the current value, the
new value and the range, and writes only when the user confirms. Repairs are shown to administrators only, and an
automation cannot confirm one: no path writes a regulation setting without a person. A request expires after
`PENDING_TTL` seconds."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .guard import WriteRefused
from .writer import WriteFailed


async def async_create_fix_flow(hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None) -> RepairsFlow:
    return ConfirmWriteFlow(data or {})


class ConfirmWriteFlow(RepairsFlow):
    def __init__(self, data: dict[str, Any]) -> None:
        self._entry_id = data.get("entry_id")
        self._pending_id = data.get("pending")

    def _writer(self):
        entry = self.hass.config_entries.async_get_entry(self._entry_id) if self._entry_id else None
        hub = getattr(entry, "runtime_data", None) if entry is not None else None
        return getattr(hub, "writer", None)

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        writer = self._writer()
        pending = writer.pending.get(self._pending_id) if writer is not None else None
        if pending is None:
            return self.async_abort(reason="expired")
        if user_input is None:
            return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}),
                                        description_placeholders=pending.placeholders)
        try:
            entry = await writer.async_confirm(self._pending_id, self.context.get("user_id"))
        except WriteRefused as err:
            return self.async_abort(reason="refused", description_placeholders={"reason": str(err)})
        except WriteFailed as err:
            return self.async_abort(reason="failed", description_placeholders={"reason": str(err)})
        return self.async_create_entry(data={"result": entry["result"]})
