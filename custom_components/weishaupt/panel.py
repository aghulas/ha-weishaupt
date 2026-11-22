"""The Weishaupt panel: the installation for administrators, organised like the vendor's controllers (device, menu,
value), with the weekly programs as a week grid and the definitions in use.

The panel is a web component built from `frontend/` (TypeScript and Lit) into `frontend/dist/weishaupt-panel.js`,
served by the integration and registered in the sidebar for administrators only; every WebSocket command below
requires an administrator. Opening the panel asks nothing from the bus. It reads on demand what no entity follows
(through the reader's queue, at its pace), enables or disables the sensors behind its rows in the entity registry,
and writes only through the writer of the entities and its guard."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from . import endpoints
from .const import DOMAIN
from .hub import Hub
from .model import Field, Message

PANEL_URL = DOMAIN  # /weishaupt
PANEL_ELEMENT = "weishaupt-panel"
PANEL_FILE = Path(__file__).parent / "frontend" / "dist" / "weishaupt-panel.js"
CARD_FILE = "weishaupt-card.js"  # the dashboard card, beside the panel
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
    for command in (ws_installations, ws_tree, ws_subscribe, ws_read_program, ws_write, ws_write_days, ws_clock,
                    ws_confirm, ws_cancel, ws_faults, ws_read_faults, ws_read_rows, ws_stop_read, ws_follow):
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
    card = PANEL_FILE.parent / CARD_FILE
    if card.is_file():
        # the dashboard card (owner's choice C1): loaded by the frontend on its own, no resource to add by hand
        from homeassistant.components.frontend import add_extra_js_url
        add_extra_js_url(hass, f"{STATIC_URL}/{CARD_FILE}?v={version}")


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

    ended: set[str] = set()  # jobs whose end this subscriber was told

    def jobs() -> dict[str, Any]:
        """Progress of the reads asked from the panel that are running, and of those that ended since last told."""
        found = {}
        for job in list(hub.read_jobs.values()):
            if job.id in ended:
                continue
            progress = hub.job_progress(job)
            found[job.id] = progress
            if progress["ended"]:
                ended.add(job.id)
        return found

    @callback
    def forward(key: str | None) -> None:
        if key is None:
            event = {"available": hub.available, "now": time.time()}
        else:
            event = {"readings": {key: _reading(hub, key)}, "now": time.time()}
            if key in members:
                event["programs"] = {members[key]: program_days(hub, members[key])}
        if progress := jobs():
            event["jobs"] = progress
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
                     if group.family == "program"},
        "jobs": jobs()}))


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
    state = hub.queue_state()  # before queueing: what these reads will wait behind
    queued = hub.async_read_once(group.members)
    connection.send_result(msg["id"], _estimate(queued, state))


# ---- writes: the writer of the entities, its guard and its confirmation, nothing else -----------------------------
#
# Every command below calls the same Writer methods as the entities (writer.py): the writes switch, the hourly limit,
# the 10 s per register, the ranges and linked bounds, the source address of the metadata, the service-tool check and
# the read-back apply unchanged. A regulation change waits for a confirmation in the panel's own dialog (`inline`)
# instead of a repair; the confirmation goes through `async_confirm`, as the repair flow does.


async def _messages(hass: HomeAssistant, language: str) -> dict[str, str]:
    from homeassistant.helpers.translation import async_get_translations
    return await async_get_translations(hass, language, "exceptions", {DOMAIN})


async def _refusal(hass: HomeAssistant, err: Exception, language: str) -> dict[str, Any]:
    """A refusal or a failure of the writer, as the entity would show it: its code and its translated message."""
    code = getattr(err, "code", "write_failed")
    placeholders = {k: str(v) for k, v in getattr(err, "placeholders", {}).items()}
    template = (await _messages(hass, language)).get(f"component.{DOMAIN}.exceptions.{code}.message", str(err))
    try:
        message = template.format(**placeholders)
    except (KeyError, IndexError, ValueError):
        message = template
    return {"status": "refused", "code": code, "message": message}


def _guard_state(hub: Hub) -> dict[str, Any]:
    writer = hub.writer
    return {"switch": writer.switch_on, "writes_last_hour": writer.guard.writes_last_hour(),
            "max_per_hour": writer.guard.max_per_hour}


def _written(hub: Hub, entry: dict[str, Any] | None, language: str) -> dict[str, Any]:
    """The result of a setting written, in the words of its logbook entry: before -> after, frame, read-back."""
    from .writer import RESULT_TEXT, _text
    if entry is None:
        return {"status": "written", "guard": _guard_state(hub)}
    spec = hub.writer.specs.get(entry["key"])
    words = RESULT_TEXT.get(language, RESULT_TEXT["en"])
    before = _text(spec, entry["before"], language) if spec and entry.get("before") is not None else None
    after = _text(spec, entry["requested"], language) if spec else str(entry["requested"])
    back = _text(spec, entry["read_back"], language) if spec and entry.get("read_back") is not None else None
    return {"status": "written", "result": entry["result"], "result_text": words.get(entry["result"], entry["result"]),
            "before": before, "after": after, "read_back": back, "frame": entry.get("frame"),
            "guard": _guard_state(hub)}


def _writer_or_error(hass: HomeAssistant, connection, msg: dict[str, Any]):
    hub = _hub(hass, connection, msg)
    if hub is None:
        return None
    if hub.writer is None:
        connection.send_error(msg["id"], "writes_disabled", "writes are not enabled in the options of the entry")
        return None
    return hub


def _language(hass: HomeAssistant, msg: dict[str, Any]) -> str:
    language = (msg.get("language") or hass.config.language or "en").split("-")[0]
    return language if language in ("en", "fr") else "en"


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/write", vol.Required("entry_id"): str,
                                  vol.Required("key"): str, vol.Required("value"): vol.Coerce(float),
                                  vol.Optional("language"): str})
@websocket_api.async_response
async def ws_write(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Set a setting (a number or a choice, by its raw value). Comfort: written and read back now. Regulation: the
    answer is `confirm` with the same facts as the repair, and nothing is written until `weishaupt/panel/confirm`."""
    from .guard import WriteRefused
    from .writer import ConfirmationPending, WriteFailed
    hub = _writer_or_error(hass, connection, msg)
    if hub is None:
        return
    language = _language(hass, msg)
    value = msg["value"]
    spec = hub.writer.specs.get(msg["key"])
    if spec is not None and spec.values is not None:
        value = int(value)
    try:
        entry = await hub.writer.async_request(msg["key"], value, connection.user.id, inline=True)
    except ConfirmationPending as pending:
        connection.send_result(msg["id"], {"status": "confirm", "pending_id": pending.pending_id,
                                           "placeholders": pending.placeholders, "kind": "setting"})
        return
    except (WriteRefused, WriteFailed) as err:
        connection.send_result(msg["id"], await _refusal(hass, err, language))
        return
    connection.send_result(msg["id"], _written(hub, entry, language))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/write_days", vol.Required("entry_id"): str,
                                  vol.Required("program"): str,
                                  vol.Required("days"): {vol.Coerce(int): str}, vol.Optional("language"): str})
@websocket_api.async_response
async def ws_write_days(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Write days of a program proven writable, as the program-day entities and `weishaupt.set_program` do: every
    day checked first, the slots read, only the changed slots written and read back (comfort, no confirmation)."""
    from .guard import WriteRefused
    from .writer import WriteFailed
    hub = _writer_or_error(hass, connection, msg)
    if hub is None:
        return
    language = _language(hass, msg)
    days = {day: text for day, text in msg["days"].items() if 1 <= day <= 7}
    try:
        done = await hub.writer.async_set_program(msg["program"], days, connection.user.id)
    except (WriteRefused, WriteFailed) as err:
        connection.send_result(msg["id"], await _refusal(hass, err, language))
        return
    from .writer import RESULT_TEXT
    words = RESULT_TEXT.get(language, RESULT_TEXT["en"])
    written = {str(day): dict(hub.writer.last_day_writes.get((msg["program"], day)) or {}) for day in days}
    for item in written.values():
        if "result" in item:
            item["result_text"] = words.get(item["result"], item["result"])
    connection.send_result(msg["id"], {"status": "written", "written": done["written"],
                                       "unchanged": done["unchanged"], "days": written, "guard": _guard_state(hub)})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/clock", vol.Required("entry_id"): str,
                                  vol.Optional("language"): str})
@websocket_api.async_response
async def ws_clock(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """The set-clock button of the panel: always a confirmation first, as the button entity."""
    from .guard import WriteRefused
    from .writer import ConfirmationPending, WriteFailed
    hub = _writer_or_error(hass, connection, msg)
    if hub is None:
        return
    try:
        await hub.writer.async_request_clock(connection.user.id, inline=True)
    except ConfirmationPending as pending:
        connection.send_result(msg["id"], {"status": "confirm", "pending_id": pending.pending_id,
                                           "placeholders": pending.placeholders, "kind": "clock"})
        return
    except (WriteRefused, WriteFailed) as err:
        connection.send_result(msg["id"], await _refusal(hass, err, _language(hass, msg)))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/confirm", vol.Required("entry_id"): str,
                                  vol.Required("pending_id"): str, vol.Optional("language"): str})
@websocket_api.async_response
async def ws_confirm(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """The user confirmed a regulation change (or the clock) in the panel's dialog: written as from the repair."""
    from .guard import WriteRefused
    from .writer import CLOCK_KEY, WriteFailed
    hub = _writer_or_error(hass, connection, msg)
    if hub is None:
        return
    language = _language(hass, msg)
    pending = hub.writer.pending.get(msg["pending_id"])
    try:
        entry = await hub.writer.async_confirm(msg["pending_id"], connection.user.id)
    except (WriteRefused, WriteFailed) as err:
        connection.send_result(msg["id"], await _refusal(hass, err, language))
        return
    if pending is not None and pending.key == CLOCK_KEY:
        from .writer import RESULT_TEXT
        words = RESULT_TEXT.get(language, RESULT_TEXT["en"])
        connection.send_result(msg["id"], {
            "status": "written", "result": entry["result"], "result_text": words.get(entry["result"], entry["result"]),
            "requested": entry["requested"],
            "frame": entry.get("frame"), "late": entry.get("late"), "guard": _guard_state(hub)})
        return
    connection.send_result(msg["id"], _written(hub, entry, language))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/cancel", vol.Required("entry_id"): str,
                                  vol.Required("pending_id"): str})
@callback
def ws_cancel(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """The user closed the panel's confirmation without confirming: the change is withdrawn, nothing is written."""
    hub = _writer_or_error(hass, connection, msg)
    if hub is not None:
        connection.send_result(msg["id"], {"withdrawn": hub.writer.drop_pending(msg["pending_id"])})


# ---- fault tables (read only) ----------------------------------------------------------------------------------


def fault_tables(hub: Hub) -> list[dict[str, Any]]:
    """Per device present: its fault memory (entries with their text), its fault counters, the fault-log entry of
    the system manager; the keys behind them, and how many of them no enabled entity reads (asked once on demand)."""
    from . import faults
    model, listened = hub.model, hub.listened()
    out = []
    for device in hub.devices.values():
        circuits = [c.circuit for c in device.circuits]
        keys: list[str] = []
        history = None
        for group in model.groups.values():
            if group.family == "fault_history" and group.device == device.id:
                pointer_name = group.pointer.message if group.pointer else "FaultHistoryPointer"
                pointer = f"{group.circuit}/{pointer_name}"
                pointer = pointer if pointer in hub.usable else None
                known = faults.texts(model, group.circuit)
                entries = faults.history(model, hub.reading, group, pointer)
                if entries is not None:
                    fields = {f.name: f for f in model.messages[group.members[0]].fields}
                    entries = [_fault_entry(entry, fields, known) for entry in entries]
                history = {"entries": entries, "ordered": bool(pointer and hub.reading(pointer) is not None)}
                keys += [*group.members, *([pointer] if pointer else [])]
        counters = [row for circuit in circuits for row in faults.counters(model, hub.reading, circuit)]
        keys += sorted({row.pop("key") for row in counters})
        log = None
        for circuit in circuits:
            if faults.log_keys(model, circuit):
                log = {"entry": faults.log_entry(model, hub.reading, circuit)}
                keys += faults.log_keys(model, circuit)
        keys = [key for key in keys if key in hub.usable]
        if not keys:
            continue
        out.append({"device": device.id, "label": device.label, "history": history, "counters": counters or None,
                    "log": log, "keys": keys, "not_listened": sum(1 for key in keys if key not in listened),
                    "to_read": len(hub.to_read_once(keys)),
                    "unread": sum(1 for key in keys if key not in hub.readings)})
    return out


def _fault_entry(entry: dict[str, Any], fields: dict[str, Field], known: dict[int, dict[str, str]]) -> dict[str, Any]:
    """An entry of a fault memory for the panel: code, text, and each value the automat stored with its label,
    unit and, for a value list, the labels of its entry."""
    values = []
    for name, value in entry.items():
        fld = fields.get(name)
        if fld is None or name in ("number", "kind"):  # already in the code (F11, W12)
            continue
        labels = (fld.value_labels or {}).get(next((r for r, n in (fld.values or {}).items() if n == value), ""))
        values.append({"label": fld.label or {"en": name}, "value": None if value is None else str(value),
                       "value_labels": labels, "unit": fld.unit})
    return {"slot": entry["slot"], "code": entry["code"], "number": entry["number"],
            "text": known.get(entry["number"]), "values": values}


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/faults", vol.Required("entry_id"): str})
@callback
def ws_faults(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """The fault tables from what the reader holds: nothing is asked from the bus."""
    hub = _hub(hass, connection, msg)
    if hub is not None:
        connection.send_result(msg["id"], fault_tables(hub))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/read_faults", vol.Required("entry_id"): str,
                                  vol.Required("device"): str})
@callback
def ws_read_faults(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Read once the fault messages of a device that no enabled entity reads, at the pace of the reader and after
    what the entities wait for, as for a program."""
    hub = _hub(hass, connection, msg)
    if hub is None:
        return
    table = next((t for t in fault_tables(hub) if t["device"] == msg["device"]), None)
    if table is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "no fault messages on this device")
        return
    state = hub.queue_state()
    queued = hub.async_read_once(tuple(table["keys"]))
    connection.send_result(msg["id"], _estimate(queued, state))


def _estimate(queued: int, state: dict[str, Any]) -> dict[str, Any]:
    """Requests really queued, their own time, and the reads already due ahead of them (the first pass after a
    start, the reader's queue): rough, at one request per gap."""
    gap = state["gap"]
    return {"queued": queued, "seconds": round(queued * gap), "ahead": state["ahead"],
            "wait": round(state["ahead"] * gap), "first_pass": state["first_pass"]}


def _reading(hub: Hub, key: str) -> dict[str, Any] | None:
    """The last reading; `kept` while it is the one kept across a reload of the entry, not yet read again; `once`
    when no enabled entity reads the message: read once on demand, not kept up to date."""
    found = hub.readings.get(key)
    return None if found is None else {"values": list(found.values), "when": found.when,
                                       "kept": key in hub.restored, "once": key not in hub.listened()}


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
    follow = followable(hass, hub)
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
            "stored_only": group.stored_only,
            "read": all(key in hub.usable for key in group.members),
            "listened": any(key in listened for key in group.members),
            "slots": len(group.members),
            "to_read": len(hub.to_read_once(group.members)),
            "edited_on": _edited_on(hub, model.shared_group(group)),
            "entity_id": links.get(f"{group.circuit}/group/{group.id}", {}).get("sensor"),
            "follow": follow.get(f"{group.circuit}/group/{group.id}"),
        } for group in model.groups.values() if group.family == "program" and group.device == device.id]
        for row in rows:
            row["follow"] = follow.get(row["key"])
            row["listened"] = any(key in listened for key in row["messages"])
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
                  "own_address": hub.own_address,
                  "capability": hub.capability,
                  "endpoint": hub.endpoint.label if hub.endpoint is not None else None,
                  "mode": endpoints.mode_of(dict(entry.data)),
                  "endpoints": [e.label for e in endpoints.endpoints_of(dict(entry.data))]},
        "definitions": {
            "version": model.version, "commit": model.commit, "source": hub.metadata_source,
            "refused": hub.metadata_refused, "named_from_metadata": _named(hass, hub),
            "not_named": sorted(hub.not_named),
            "mismatches": [{"key": m.key, "reason": m.reason, "detail": m.detail} for m in hub.mismatches],
            "messages": len(model.messages), "usable": len(hub.usable), "not_usable": _not_usable(hub)},
        "writes": None if writer is None else {
            "switch": writer.switch_on, "capability": writer.capability,
            "writes_last_hour": writer.guard.writes_last_hour(), "max_per_hour": writer.guard.max_per_hour,
            "read_only": [{"key": key, "reason": reason} for key, reason in sorted(writer.not_writable.items())],
            "switch_entity_id": links.get("writes", {}).get("switch"),
            "clock_writable": writer.clock_writable},
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


def _edited_on(hub: Hub, group) -> dict[str, Any] | None:
    """Where a value read from another device's store is changed: that device and its program (or message)."""
    if group is None:
        return None
    return {"device": hub.model.devices[group.device].label, "key": group.key, "label": group.label}


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


def _writable(hub: Hub, message: Message, write, through: Message | None, fld: Field) -> dict[str, Any]:
    """How a setting is written: the message the writer knows it by, whether this installation offers the write
    (writes enabled, the write definition loaded, a range), why not, the raw values of a choice."""
    writer = hub.writer
    spec = writer.specs.get(message.key) if writer is not None else None
    return {
        "risk": write.risk, "source": write.source, "proof": write.proof,
        "through": through.circuit if through else None, "key": message.key,
        "offered": spec is not None,
        "why_not": None if spec is not None else (
            "writes_disabled" if writer is None else writer.not_writable.get(message.key, "not_offered")),
        "register": f"{spec.register[:2]} {spec.register[2:]}" if spec else None,
        "address": spec.zz if spec else None,
        "minimum": spec.minimum if spec else None, "maximum": spec.maximum if spec else None,
        "step": spec.step if spec else None,
        "options": None if spec is None or spec.values is None else [
            {"raw": raw, "name": name, "label": (spec.value_labels or {}).get(raw, {"en": name})}
            for raw, name in sorted(spec.values.items())],
    }


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
        "writable": None if write is None else _writable(hub, writable, write, through, fld),
        "messages": [message.key, *(m.key for m in twins)],  # read by any: the first with a reading is shown
        "read": any(m in hub.usable for m in [message.key, *(t.key for t in twins)]), "passive": message.passive,
        "edited_on": None if not message.shared_with or message.shared_with not in hub.model.messages else {
            "device": hub.model.devices[hub.model.messages[message.shared_with].device].label,
            "key": message.shared_with},
        "absent": fld.absent if fld.absent is not None else (ABSENT.get(device_type) if fld.unit == "°C" else None),
        "entity_id": next((entities[p] for p in LINK_ORDER if p in entities), None),
    }


# ---- reads on demand for a menu, a device or the installation, and following entities --------------------------------
#
# Reads only: the keys go through `Hub.async_read_job`, the same queue, pace and priority as *Read now* of a program
# (after what the entities wait for, one request at a time). Following an entity enables or disables it in the entity
# registry, as its own settings dialog does; Home Assistant reloads the entry 30 s after an entity is enabled.

def _row_messages(hub: Hub) -> list[tuple[Any, Message, list[Message]]]:
    """(device, message, the messages reading the same register) of every row the tree shows."""
    twins: dict[str, list[Message]] = {}
    for message in hub.model.messages.values():
        if message.same_as:
            twins.setdefault(message.same_as, []).append(message)
    return [(device, message, twins.get(message.key, [])) for device in hub.devices.values()
            for message in hub.model.messages.values()
            if message.device == device.id and message.family != "program" and (message.read or message.passive)
            and not message.same_as and any(fld.shown for fld in message.fields)]


def scope_keys(hub: Hub, device: str | None = None, menu: str | None = None) -> list[str]:
    """The messages of the rows of a menu (with `device`), a device, or every device, that no enabled entity reads:
    what a read on demand asks. A row read through another message of its register counts as read."""
    listened = hub.listened()
    keys: list[str] = []
    for found, message, twins in _row_messages(hub):
        if device is not None and found.id != device or menu is not None and message.menu != menu:
            continue
        if any(m.key in listened for m in [message, *twins]):
            continue
        if message.key not in keys:
            keys.append(message.key)
    return hub.to_read_once(keys)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/read_rows", vol.Required("entry_id"): str,
                                  vol.Optional("device"): str, vol.Optional("menu"): str,
                                  vol.Optional("start", default=False): bool})
@callback
def ws_read_rows(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Read once the rows no enabled entity reads, of a menu (`device` and `menu`), a device, or the installation
    (neither). Without `start`, only what it would cost: the requests, their time, what they wait behind."""
    hub = _hub(hass, connection, msg)
    if hub is None:
        return
    device, menu = msg.get("device"), msg.get("menu")
    if device is not None and device not in hub.devices or menu is not None and device is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "no such device on the bus")
        return
    keys = scope_keys(hub, device, menu)
    state = hub.queue_state()
    if not msg["start"]:
        connection.send_result(msg["id"], _estimate(len(keys), state))
        return
    job = hub.async_read_job(keys)
    connection.send_result(msg["id"], {**_estimate(len(job.keys), state), "job": hub.job_progress(job)})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/stop_read", vol.Required("entry_id"): str,
                                  vol.Required("job"): str})
@callback
def ws_stop_read(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Withdraw what a read on demand has not asked yet; the request being made finishes."""
    hub = _hub(hass, connection, msg)
    if hub is None:
        return
    job = hub.async_stop_job(msg["job"])
    if job is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "no such read")
        return
    connection.send_result(msg["id"], hub.job_progress(job))


# entities disabled by Home Assistant itself (their config entry, their device): not the panel's to enable
_BLOCKED = (er.RegistryEntryDisabler.CONFIG_ENTRY, er.RegistryEntryDisabler.DEVICE)


def followable(hass: HomeAssistant, hub: Hub) -> dict[str, dict[str, Any]]:
    """Key of a row (`<circuit>/<message>/<field>`) or program (`<circuit>/group/<id>`) -> its sensor in the
    registry, enabled or not: the entity that makes the reader keep it up to date."""
    registry = er.async_get(hass)
    prefix = f"{hub.entry.entry_id}_"
    defaults = {d.key: (d.platform, d.enabled_default) for d in hub.model.value_entities}
    defaults |= {d.key: ("sensor", d.enabled_default) for d in hub.model.group_entities}
    found = {}
    for item in er.async_entries_for_config_entry(registry, hub.entry.entry_id):
        key = item.unique_id.removeprefix(prefix)
        if not item.unique_id.startswith(prefix) or defaults.get(key, (None,))[0] != item.domain:
            continue
        found[key] = {"entity_id": item.entity_id, "enabled": item.disabled_by is None,
                      "default": defaults[key][1], "blocked": item.disabled_by in _BLOCKED}
    return found


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "weishaupt/panel/follow", vol.Required("entry_id"): str,
                                  vol.Optional("enable", default=[]): [str],
                                  vol.Optional("disable", default=[]): [str]})
@callback
def ws_follow(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Enable (follow) or disable the sensors of rows and programs, all in one go: Home Assistant reloads the entry
    once, 30 s after the last entity enabled. Only this entry's own sensors; one disabled by its device or its
    config entry is left as it is."""
    hub = _hub(hass, connection, msg)
    if hub is None:
        return
    from homeassistant.config_entries import RELOAD_AFTER_UPDATE_DELAY
    registry = er.async_get(hass)
    known = {item["entity_id"]: item for item in followable(hass, hub).values()}
    changed: dict[str, list[str]] = {"enabled": [], "disabled": []}
    refused = []
    for wanted, entity_ids in ((True, msg["enable"]), (False, msg["disable"])):
        for entity_id in entity_ids:
            item = known.get(entity_id)
            if item is None or item["blocked"]:
                refused.append({"entity_id": entity_id, "reason": "not_followable" if item is None else "blocked"})
                continue
            if item["enabled"] == wanted:
                continue
            registry.async_update_entity(
                entity_id, disabled_by=None if wanted else er.RegistryEntryDisabler.USER)
            changed["enabled" if wanted else "disabled"].append(entity_id)
    connection.send_result(msg["id"], {**changed, "refused": refused, "reload": bool(changed["enabled"]),
                                       "reload_after": RELOAD_AFTER_UPDATE_DELAY})
