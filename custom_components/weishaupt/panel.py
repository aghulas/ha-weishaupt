"""The Weishaupt panel: a read-only view of the installation for administrators, organised like the vendor's
controllers (device, menu, value), with the weekly programs as a week grid and the definitions in use.

The panel is a web component built from `frontend/` (TypeScript and Lit) into `frontend/dist/weishaupt-panel.js`,
served by the integration and registered in the sidebar for administrators only. It reads through the WebSocket
commands below, which only look at what the integration already holds: opening the panel asks nothing from the bus,
and the panel writes nothing (a change goes through the entity, which the row links to)."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .hub import Hub
from .model import Field, Message

PANEL_URL = DOMAIN  # /weishaupt
PANEL_ELEMENT = "weishaupt-panel"
PANEL_FILE = Path(__file__).parent / "frontend" / "dist" / "weishaupt-panel.js"
STATIC_URL = f"/{DOMAIN}_panel"
PANEL_ICON = "mdi:fire"
PANEL_TITLE = "Weishaupt"
DAYS = range(1, 8)  # ISO weekdays, Monday first
# platforms of the entities a row links to, the setting first: a change is made there
LINK_ORDER = ("number", "select", "text", "sensor", "binary_sensor")


async def async_setup_panel(hass: HomeAssistant, version: str) -> None:
    """Register the WebSocket commands, and the panel when Home Assistant's frontend runs (not in the tests of
    the entities, nor on an installation without it). The URL of the file carries the version, so that an update
    is not hidden by the browser's cache."""
    for command in (ws_installations, ws_tree, ws_subscribe, ws_read_program):
        websocket_api.async_register_command(hass, command)
    if "frontend" not in hass.config.components or hass.http is None or not PANEL_FILE.is_file():
        return
    from homeassistant.components import panel_custom
    from homeassistant.components.http import StaticPathConfig

    await hass.http.async_register_static_paths([StaticPathConfig(STATIC_URL, str(PANEL_FILE.parent), True)])
    await panel_custom.async_register_panel(
        hass, frontend_url_path=PANEL_URL, webcomponent_name=PANEL_ELEMENT, sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON, module_url=f"{STATIC_URL}/{PANEL_FILE.name}?v={version}", require_admin=True,
        config_panel_domain=DOMAIN)


def _hubs(hass: HomeAssistant) -> dict[str, Any]:
    return {entry.entry_id: entry for entry in hass.config_entries.async_loaded_entries(DOMAIN)}


def _hub(hass: HomeAssistant, connection, msg: dict[str, Any]) -> Hub | None:
    entry = _hubs(hass).get(msg["entry_id"])
    if entry is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "no loaded Weishaupt entry with this id")
        return None
    return entry.runtime_data


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/installations"})
@callback
def ws_installations(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """The loaded entries: one installation (one ebusd) each."""
    connection.send_result(msg["id"], [
        {"entry_id": entry.entry_id, "title": entry.title} for entry in _hubs(hass).values()])


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/tree", vol.Required("entry_id"): str})
@callback
def ws_tree(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """What does not change while the entry is loaded: devices, menus, rows, programs, definitions."""
    hub = _hub(hass, connection, msg)
    if hub is not None:
        connection.send_result(msg["id"], tree(hass, hub))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/subscribe",
                                  vol.Required("entry_id"): str})
@callback
def ws_subscribe(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """The readings and program days now, then each change as the reader gets it. Asks nothing from the bus."""
    hub = _hub(hass, connection, msg)
    if hub is None:
        return
    members = {key: group.key for group in hub.model.groups.values() if group.family == "program"
               for key in group.members}

    @callback
    def forward(key: str | None) -> None:
        if key is None:
            event = {"available": hub.available, "now": time.time()}
        else:
            event = {"readings": {key: _reading(hub, key)}, "now": time.time()}
            if key in members:
                event["programs"] = {members[key]: program_days(hub, members[key])}
        connection.send_message(websocket_api.event_message(msg["id"], event))

    stop_observing = hub.async_observe(forward)

    @callback
    def reloaded() -> None:
        # the entry unloads (a reload, an option changed): the panel asks the new hub for its tree and readings
        stop()
        connection.subscriptions.pop(msg["id"], None)
        connection.send_message(websocket_api.event_message(msg["id"], {"reloaded": True, "now": time.time()}))

    stop_closing = hub.async_on_close(reloaded)

    @callback
    def stop() -> None:
        stop_observing()
        stop_closing()

    connection.subscriptions[msg["id"]] = stop
    connection.send_result(msg["id"])
    connection.send_message(websocket_api.event_message(msg["id"], {
        "available": hub.available, "now": time.time(),
        "readings": {key: _reading(hub, key) for key in hub.readings},
        "programs": {key: program_days(hub, key) for key, group in hub.model.groups.items()
                     if group.family == "program"}}))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/read_program",
                                  vol.Required("entry_id"): str, vol.Required("program"): str})
@callback
def ws_read_program(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Read once the slots of a program no enabled entity reads, for the week grid: one request per slot at the
    pace of the reader, after what the entities wait for. Read once: not again until asked again."""
    hub = _hub(hass, connection, msg)
    if hub is None:
        return
    group = hub.model.groups.get(msg["program"])
    if group is None or group.family != "program":
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "no program with this key")
        return
    queued = hub.async_read_once(group.members)
    connection.send_result(msg["id"], {"queued": queued, "seconds": round(queued * max(hub.request_gap, 1.0))})


def _reading(hub: Hub, key: str) -> dict[str, Any] | None:
    """The last reading; `kept` while it is the one kept across a reload of the entry, not yet read again."""
    found = hub.readings.get(key)
    return None if found is None else {"values": list(found.values), "when": found.when,
                                       "kept": key in hub.restored}


def program_days(hub: Hub, group_key: str) -> dict[str, list[list[str]] | None]:
    """Day (1 Monday … 7 Sunday) -> its enabled ranges [from, to] in slot order; None while a slot of the day is
    unread. A slot is shown only when both of its times are enabled, as the program sensor does."""
    group = hub.model.groups[group_key]
    days: dict[str, list[list[str]] | None] = {}
    for day in DAYS:
        slots: list[tuple[int, list[str]]] = []
        complete = True
        for key in group.members:
            message = hub.model.messages[key]
            position = message.position or {}
            if position.get("day") != day:
                continue
            reading = hub.readings.get(key)
            if reading is None:
                complete = False
                break
            fields = {fld.name: reading.values[fld.index] for fld in message.fields if fld.index < len(reading.values)}
            if fields.get("fromenabled") == "Enabled" and fields.get("toenabled") == "Enabled":
                slots.append((position.get("slot", 0), [fields["fromtime"], fields["totime"]]))
        days[str(day)] = [r for _, r in sorted(slots)] if complete else None
    return days


def tree(hass: HomeAssistant, hub: Hub) -> dict[str, Any]:
    """Devices present on the bus with their menus, rows and programs, and the state of the definitions."""
    model, entry = hub.model, hub.entry
    links = _links(hass, entry.entry_id)
    writer = hub.writer
    listened = hub.listened()
    # messages that read the same register as another one of their device (`same_as`): shown on one row
    twins: dict[str, list[Message]] = {}
    for message in model.messages.values():
        if message.same_as:
            twins.setdefault(message.same_as, []).append(message)
    devices = []
    for device in hub.devices.values():
        scan = hub.address_of(device)
        messages = [m for m in model.messages.values() if m.device == device.id]
        rows = [_row(hub, message, fld, links, twins.get(message.key, []), device.type) for message in messages
                if message.family != "program" and (message.read or message.passive) and not message.same_as
                for fld in message.fields if fld.shown]
        programs = [{
            "key": group.key, "label": group.label,
            "writable": writer is not None and group.key in writer.programs,
            "read": all(key in hub.usable for key in group.members),
            "listened": any(key in listened for key in group.members),
            "slots": len(group.members),
            "entity_id": links.get(f"{group.circuit}/group/{group.id}", {}).get("sensor"),
        } for group in model.groups.values() if group.family == "program" and group.device == device.id]
        used = {row["menu"] for row in rows} | ({"programs"} if programs else set())
        menus = [{"id": menu.id, "parent": menu.parent, "label": menu.label}
                 for menu in model.menus.get(device.type, ())]
        devices.append({
            "id": device.id, "type": device.type, "label": device.label,
            "addresses": [c.address for c in device.circuits if c.address != "fe"],
            "software": scan.software if scan else None, "hardware": scan.hardware if scan else None,
            "menus": [menu for menu in menus if menu["id"] in used or _has_child(menu["id"], menus, used)],
            "rows": rows, "programs": programs})
    clock = links.get("broadcast/Datetime/offset", {}).get("sensor")
    return {
        "entry_id": entry.entry_id, "title": entry.title,
        "ebusd": {"version": hub.info.version if hub.info else None, "available": hub.available,
                  "own_address": hub.own_address},
        "definitions": {
            "version": model.version, "commit": model.commit, "source": hub.metadata_source,
            "refused": hub.metadata_refused, "named_from_metadata": _named(hass, hub),
            "not_named": sorted(hub.not_named),
            "mismatches": [{"key": m.key, "reason": m.reason, "detail": m.detail} for m in hub.mismatches],
            "messages": len(model.messages), "usable": len(hub.usable), "not_usable": _not_usable(hub)},
        "writes": None if writer is None else {
            "switch": writer.switch_on, "capability": writer.capability,
            "writes_last_hour": writer.guard.writes_last_hour(), "max_per_hour": writer.guard.max_per_hour,
            "switch_entity_id": links.get("writes", {}).get("switch")},
        "clock": {"entity_id": clock, "set_entity_id": links.get("broadcast/Datetime/set", {}).get("button")},
        "unknown_addresses": [a.address for a in hub.unknown_slaves],
        "devices": devices,
    }


def _named(hass: HomeAssistant, hub: Hub) -> list[dict[str, Any]]:
    """The entities named from the metadata, by their entity ids in the registry."""
    registry = er.async_get(hass)
    found = []
    for item in er.async_entries_for_config_entry(registry, hub.entry.entry_id):
        if item.unique_id in hub.named_entities:
            found.append({"entity_id": item.entity_id, "disabled": item.disabled_by is not None})
    return sorted(found, key=lambda e: e["entity_id"])


def _not_usable(hub: Hub) -> list[dict[str, str]]:
    """Each message of the metadata that is not read, and why: write-only, its device is not on the bus, or ebusd
    did not load it as described."""
    bad = {m.key for m in hub.mismatches}
    out = []
    for key, message in hub.model.messages.items():
        if key in hub.usable:
            continue
        if not (message.read or message.passive):
            reason = "write_only"
        elif message.circuit not in hub.circuits:
            reason = "device_absent"
        elif key in bad:
            reason = "mismatch"
        else:
            reason = "other"
        out.append({"key": key, "reason": reason})
    return out


def _has_child(menu_id: str, menus: list[dict[str, Any]], used: set[str]) -> bool:
    children = [m for m in menus if m["parent"] == menu_id]
    return any(child["id"] in used or _has_child(child["id"], menus, used) for child in children)


def _links(hass: HomeAssistant, entry_id: str) -> dict[str, dict[str, str]]:
    """Key of the integration (unique id without the entry) -> platform -> entity id, enabled entities only."""
    found: dict[str, dict[str, str]] = {}
    for item in er.async_entries_for_config_entry(er.async_get(hass), entry_id):
        if item.disabled_by is None and item.unique_id.startswith(f"{entry_id}_"):
            found.setdefault(item.unique_id.removeprefix(f"{entry_id}_"), {})[item.domain] = item.entity_id
    return found


# Values a boiler sends for a temperature sensor that is not fitted, and those of the system manager and the
# heating modules (release notice of the definitions, known limits). Until the metadata marks them (`absent` on a
# field), the panel shows exactly these values of a °C field on these kinds of device as "no sensor".
ABSENT = {"boiler": -40.0, "module": -100.0, "manager": -100.0, "system": -100.0}


def _row(hub: Hub, message: Message, fld: Field, links: dict[str, dict[str, str]], twins: list[Message],
         device_type: str) -> dict[str, Any]:
    key = f"{message.key}/{fld.name}"
    shown = len([f for f in message.fields if f.shown]) == 1
    label = message.label if shown or fld.label is None else {
        lang: f"{message.label[lang]} – {text}" for lang, text in fld.label.items()}
    # a register also read by another message of the device: the value of whichever is read, the write conditions
    # of the writable one, and its entity, where the change is made
    writable = next((m for m in [message, *twins] if m.write is not None), None)
    write = writable.write if writable else None
    through = writable if writable is not None and writable is not message else None
    other = through.field(fld.name) if through else None
    minimum = next((v for v in (fld.minimum, other.minimum if other else None, write.minimum if write else None)
                    if v is not None), None)
    maximum = next((v for v in (fld.maximum, other.maximum if other else None, write.maximum if write else None)
                    if v is not None), None)
    step = next((v for v in (fld.step, other.step if other else None, write.step if write else None)
                 if v is not None), None)
    keys = [key, *(f"{m.key}/{fld.name}" for m in twins)]
    entities = {platform: entity_id for k in reversed(keys) for platform, entity_id in links.get(k, {}).items()}
    return {
        "key": key, "message": message.key, "index": fld.index, "menu": message.menu, "kind": fld.kind,
        "label": label, "description": fld.description if not shown and fld.description else message.description,
        "unit": fld.unit, "type": fld.type,
        "values": None if fld.values is None else {
            name: (fld.value_labels or {}).get(raw, {"en": name}) for raw, name in fld.values.items()},
        "range": None if minimum is None and maximum is None else {"min": minimum, "max": maximum, "step": step},
        "writable": None if write is None else {"risk": write.risk, "source": write.source, "proof": write.proof,
                                                "through": through.circuit if through else None},
        "messages": [message.key, *(m.key for m in twins)],  # read by any: the first with a reading is shown
        "read": any(m in hub.usable for m in [message.key, *(t.key for t in twins)]), "passive": message.passive,
        "absent": fld.absent if fld.absent is not None else (ABSENT.get(device_type) if fld.unit == "°C" else None),
        "entity_id": next((entities[p] for p in LINK_ORDER if p in entities), None),
    }
