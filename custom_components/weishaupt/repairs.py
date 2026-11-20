"""Confirmation of a change of a regulation setting, and of the removal of the entities left by version 0.1.

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
from homeassistant.helpers import entity_registry as er

from . import clock
from .guard import WriteRefused
from .writer import CLOCK_KEY, WriteFailed, _text


async def async_create_fix_flow(hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None) -> RepairsFlow:
    if (data or {}).get("kind") == "old_entities":
        return RemoveOlderEntitiesFlow(data or {})
    if (data or {}).get("kind") == "device_absent":
        return RemoveAbsentDeviceFlow(data or {})
    if (data or {}).get("kind") == "ebusd_choice":
        return EbusdChoiceFlow(data or {})
    return ConfirmWriteFlow(data or {})


class EbusdChoiceFlow(RepairsFlow):
    """The ebusd in use does not answer and another one does: use that one (pinned), or follow the running one.
    Only the entry changes, and it reloads; no add-on is started or stopped, nothing is sent to the bus."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._entry_id = data.get("entry_id")

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return await self.async_step_choose()

    async def async_step_choose(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        from homeassistant.helpers import issue_registry as ir
        from homeassistant.helpers import selector

        from . import endpoints
        from .const import DOMAIN
        entry = self.hass.config_entries.async_get_entry(self._entry_id) if self._entry_id else None
        if entry is None:
            return self.async_abort(reason="no_entry")
        data = dict(entry.data)
        if user_input is not None:
            endpoints.apply_choice(self.hass, entry, user_input["use"])
            ir.async_delete_issue(self.hass, DOMAIN, endpoints.issue_not_running(entry.entry_id))
            return self.async_create_entry(data={}, description="switched")
        in_use = endpoints.current(data)
        surveys = await endpoints.survey(endpoints.endpoints_of(data))
        answering = [s.endpoint for s in surveys if s.answers and s.endpoint.key != in_use.key]
        if not answering:
            return self.async_abort(reason="none_answers")
        options = [selector.SelectOptionDict(value=endpoints.MODE_FOLLOW, label="follow")] + [
            selector.SelectOptionDict(value=e.key, label=e.label) for e in answering]
        schema = vol.Schema({vol.Required("use", default=endpoints.MODE_FOLLOW): selector.SelectSelector(
            selector.SelectSelectorConfig(options=options, translation_key="ebusd_choice"))})
        return self.async_show_form(step_id="choose", data_schema=schema,
                                    description_placeholders={"label": in_use.label})


class RemoveAbsentDeviceFlow(RepairsFlow):
    """A device missing from the bus for days: removed with its entities only when the user confirms, and only if
    it is still missing then."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._entry_id = data.get("entry_id")
        self._device = data.get("device")

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        from homeassistant.helpers import device_registry as dr
        from homeassistant.helpers import issue_registry as ir

        from .const import DOMAIN
        from .devices import issue_id, registered
        entry = self.hass.config_entries.async_get_entry(self._entry_id) if self._entry_id else None
        if entry is None:
            return self.async_abort(reason="no_entry")
        watch = self.hass.data.get(f"{DOMAIN}_device_watch", {}).get(entry.entry_id)
        device = registered(self.hass, entry).get(self._device or "")
        if device is None or watch is None or self._device not in watch.absent:
            ir.async_delete_issue(self.hass, DOMAIN, issue_id(entry, self._device or ""))
            return self.async_abort(reason="device_back")
        name = device.name_by_user or device.name or self._device
        if user_input is None:
            return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}),
                                        description_placeholders={"device": name})
        dr.async_get(self.hass).async_update_device(device.id, remove_config_entry_id=entry.entry_id)
        watch.absent.pop(self._device, None)
        ir.async_delete_issue(self.hass, DOMAIN, issue_id(entry, self._device))
        return self.async_create_entry(data={}, description="removed", description_placeholders={"device": name})


class RemoveOlderEntitiesFlow(RepairsFlow):
    """The entities left by version 0.1: listed, and removed from the registry only when the user confirms."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._entry_id = data.get("entry_id")

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        from . import OLD_ENTITIES_SHOWN, older_entities, update_older_issue
        entry = self.hass.config_entries.async_get_entry(self._entry_id) if self._entry_id else None
        if entry is None:
            return self.async_abort(reason="no_entry")
        older = older_entities(self.hass, entry)  # what is there now, not what the issue said
        if not older:
            update_older_issue(self.hass, entry)
            return self.async_abort(reason="nothing_left")
        if user_input is None:
            shown = "\n".join(f"- `{entity_id}`" for entity_id in older[:OLD_ENTITIES_SHOWN])
            if len(older) > OLD_ENTITIES_SHOWN:
                shown += f"\n- … ({len(older) - OLD_ENTITIES_SHOWN})"
            return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}),
                                        description_placeholders={"count": str(len(older)), "entities": shown})
        registry = er.async_get(self.hass)
        for entity_id in older:
            registry.async_remove(entity_id)
        update_older_issue(self.hass, entry)
        return self.async_create_entry(data={}, description="removed",
                                       description_placeholders={"count": str(len(older))})


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
            shown = dict(pending.placeholders)
            if pending.key == CLOCK_KEY:  # the time it would send if confirmed now: second 00 of the next minute
                shown["send_at"] = clock.next_minute(writer._now()).strftime("%H:%M:%S")
            return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}),
                                        description_placeholders=shown)
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
