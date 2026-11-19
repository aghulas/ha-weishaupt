"""Confirmation of a change of a regulation setting.

Setting a regulation setting creates a fixable repair issue; its flow shows the device, the setting, the current
value, the new value, the range and step, the bus address, the register and the source address, and writes only
when the user confirms. It ends with what was done: written and read back, unchanged, not taken over, refused.
Repairs are shown to administrators only, and an automation cannot confirm one: no path writes a regulation
setting without a person. A request expires after `PENDING_TTL` seconds."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .guard import WriteRefused
from .writer import CLOCK_KEY, WriteFailed, _text


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
        placeholders = dict(pending.placeholders)
        try:
            entry = await writer.async_confirm(self._pending_id, self.context.get("user_id"))
        except WriteRefused as err:
            return self.async_abort(reason="refused", description_placeholders={"reason": str(err)})
        except WriteFailed as err:
            known = ("expired", "not_taken", "write_failed", "no_read_back", "clock_late")
            reason = err.code if err.code in known else "refused"
            return self.async_abort(reason=reason, description_placeholders=placeholders | {
                "reason": err.placeholders.get("reason", str(err)), "read_back": err.placeholders.get("read_back", "-"),
                "late": err.placeholders.get("late", "-")})
        if entry["key"] == CLOCK_KEY:
            return self.async_create_entry(data={"result": entry["result"]}, description="sent",
                                           description_placeholders=placeholders | {
                                               "sent": entry["requested"], "telegram": entry["frame"],
                                               "late_ms": str(round(entry.get("late", 0) * 1000))})
        spec = writer.specs[entry["key"]]
        read_back = entry.get("read_back")
        # A successful flow ends as an entry: Home Assistant titles its dialog "Success" and deletes the issue; an
        # abort would be titled with the generic "Repair issue", which the frontend does not let an integration
        # change.
        return self.async_create_entry(
            data={"result": entry["result"]},
            description="unchanged" if entry["result"] == "unchanged" else "written",
            description_placeholders=placeholders | {
                "read_back": "-" if read_back is None else _text(spec, read_back, writer._language()),
                "telegram": entry["frame"]})
