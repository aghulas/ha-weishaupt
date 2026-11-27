"""The panel: its WebSocket commands (read only, admin only, nothing asked from the bus) and its registration."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.weishaupt import panel
from custom_components.weishaupt.model import METADATA_FILE
from ha_common import make_entry, settled, setup
from test_ha_writes import telegram_log
from test_vendor_codes import _without_codes


async def _loaded(hass, fake, tmp_path, **options):
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=telegram_log(tmp_path / "t.db"), **options)
    await setup(hass, entry)
    await settled(hass, entry)
    return entry


async def test_tree_shows_devices_menus_rows_and_programs(hass, fake, tmp_path, hass_ws_client):
    entry = await _loaded(hass, fake, tmp_path)
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "weishaupt/panel/installations"})
    answer = await client.receive_json()
    assert answer["result"] == [{"entry_id": entry.entry_id, "title": "Weishaupt"}]
    await client.send_json({"id": 2, "type": "weishaupt/panel/tree", "entry_id": entry.entry_id})
    tree = (await client.receive_json())["result"]
    assert tree["definitions"]["version"] == entry.runtime_data.model.version
    assert tree["definitions"]["source"] == "bundled" and tree["writes"]["switch"] is False
    devices = {d["id"]: d for d in tree["devices"]}
    module = devices["module2"]
    assert module["label"]["fr"] and module["addresses"] == ["51"]
    menus = [m["id"] for m in module["menus"]]
    assert "settings" in menus
    row = next(r for r in module["rows"] if r["key"] == "em2/RoomNormalTemp/value")
    assert row["menu"] == "settings" and row["unit"] == "°C" and row["read"]
    assert row["range"] == {"min": 16, "max": 35, "step": 0.5}
    assert row["writable"]["risk"] == "comfort" and row["writable"]["source"] == "ff"
    assert row["description"]["fr"]
    # the row links to the setting, where a change is made
    assert row["entity_id"].startswith("number.")
    # every menu of a row is in the tree, and no program slot is a row
    assert all(r["menu"] in menus for r in module["rows"])
    room = devices["room1"]
    assert not [r for r in room["rows"] if "Program" in r["message"] and r["kind"] == "program_slot"]
    programs = {p["key"]: p for p in room["programs"]}
    assert programs["fs1/heating1"]["writable"] and "programs" in [m["id"] for m in room["menus"]]
    assert programs["fs1/heating1"]["listened"] and not programs["fs1/heating2"]["listened"]
    assert any(not p["writable"] for d in tree["devices"] for p in d["programs"])  # shown all the same


async def test_subscribe_sends_readings_and_asks_nothing(hass, fake, tmp_path, hass_ws_client):
    entry = await _loaded(hass, fake, tmp_path)
    hub = entry.runtime_data
    listened, asked = hub.listened(), len(fake.reads_of())
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "weishaupt/panel/subscribe", "entry_id": entry.entry_id})
    assert (await client.receive_json())["success"]
    first = (await client.receive_json())["event"]
    assert first["available"] and first["readings"]["em2/RoomNormalTemp"]["values"] == ["21.5"]
    days = first["programs"]["fs1/heating1"]
    assert set(days) == {str(d) for d in range(1, 8)} and days["1"] == [["06:30", "18:00"]]
    # a reading of the reader is forwarded as it comes
    hub.store("em2/RoomNormalTemp", ("22.0",))
    event = (await client.receive_json())["event"]
    assert event["readings"]["em2/RoomNormalTemp"]["values"] == ["22.0"]
    # nothing more is listened to, nothing more read than the reader does anyway
    assert hub.listened() == listened
    assert len(fake.reads_of()) - asked <= len(listened)
    await client.send_json({"id": 2, "type": "unsubscribe_events", "subscription": 1})
    assert (await client.receive_json())["success"]
    assert hub._observers == []


async def test_commands_are_for_administrators(hass, fake, tmp_path, hass_ws_client, hass_read_only_access_token):
    entry = await _loaded(hass, fake, tmp_path)
    client = await hass_ws_client(hass, hass_read_only_access_token)
    await client.send_json({"id": 1, "type": "weishaupt/panel/tree", "entry_id": entry.entry_id})
    answer = await client.receive_json()
    assert not answer["success"] and answer["error"]["code"] == "unauthorized"
    admin = await hass_ws_client(hass)
    await admin.send_json({"id": 1, "type": "weishaupt/panel/tree", "entry_id": "nope"})
    answer = await admin.receive_json()
    assert not answer["success"] and answer["error"]["code"] == "not_found"


async def test_panel_registered_for_administrators_when_the_frontend_runs(hass, tmp_path):
    built = tmp_path / "weishaupt-panel.js"
    built.write_text("")
    (tmp_path / "weishaupt-card.js").write_text("")
    hass.config.components.add("frontend")
    hass.http = MagicMock(async_register_static_paths=AsyncMock())
    with patch("homeassistant.components.panel_custom.async_register_panel", AsyncMock()) as register, \
            patch.object(panel, "PANEL_FILE", built), \
            patch("homeassistant.components.frontend.add_extra_js_url") as extra:
        await panel.async_setup_panel(hass, "0.5.0b1")
    # the dashboard card is loaded by the frontend itself, its version in the URL
    assert extra.call_args.args[1] == "/weishaupt_panel/weishaupt-card.js?v=0.5.0b1"
    kwargs = register.call_args.kwargs
    assert kwargs["require_admin"] is True and kwargs["frontend_url_path"] == "weishaupt"
    assert kwargs["webcomponent_name"] == "weishaupt-panel"
    assert kwargs["module_url"] == "/weishaupt_panel/weishaupt-panel.js?v=0.5.0b1"
    path = hass.http.async_register_static_paths.call_args.args[0][0]
    assert path.url_path == "/weishaupt_panel" and path.cache_headers is True


async def test_no_panel_without_the_frontend(hass):
    hass.http = MagicMock(async_register_static_paths=AsyncMock())
    with patch("homeassistant.components.panel_custom.async_register_panel", AsyncMock()) as register:
        await panel.async_setup_panel(hass, "0.5.0b1")
    register.assert_not_called()


async def test_rows_share_a_register_and_mark_absent_sensors(hass, fake, tmp_path, hass_ws_client):
    """System manager › circuit 1: the setpoints are read through em1 (same register as ka), changed there; a
    boiler's °C field with -40 and a manager's with -100 is "no sensor" (release notice), until the metadata says."""
    entry = await _loaded(hass, fake, tmp_path)
    tree = panel.tree(hass, entry.runtime_data)
    devices = {d["id"]: d for d in tree["devices"]}
    manager = next(d for d in tree["devices"] if d["type"] == "manager")
    row = next(r for r in manager["rows"] if r["message"] == "ka/RoomNormalTemp")
    assert row["messages"] == ["ka/RoomNormalTemp", "em1/RoomNormalTemp"]
    assert row["writable"]["through"] == "em1" and row["entity_id"].startswith("number.")
    assert row["range"]["min"] is not None
    assert "em1/RoomNormalTemp" in entry.runtime_data.readings  # read through the number of em1
    dhw = next(r for r in devices["boiler1"]["rows"] if r["message"] == "bc1/DHWTemp")
    assert dhw["absent"] == -40.0 and row["absent"] == -100.0


async def test_a_program_is_read_once_for_the_grid(hass, fake, tmp_path, hass_ws_client):
    """A program no enabled entity reads: one request per slot when asked, once, after the entities' reads."""
    entry = await _loaded(hass, fake, tmp_path)
    hub = entry.runtime_data
    members = hub.model.groups["fs2/heating1"].members
    assert not any(key in hub.readings for key in members)
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "weishaupt/panel/read_program", "entry_id": entry.entry_id,
                            "program": "fs2/heating1"})
    answer = (await client.receive_json())["result"]
    assert answer["queued"] == 21 and answer["ahead"] >= 0 and answer["wait"] == answer["ahead"] * 1
    await settled(hass, entry)
    from ha_common import wait_until
    await wait_until(lambda: all(key in hub.readings for key in members))
    assert panel.program_days(hub, "fs2/heating1")["1"] is not None
    reads = len(fake.reads_of())
    await client.send_json({"id": 2, "type": "weishaupt/panel/read_program", "entry_id": entry.entry_id,
                            "program": "nope"})
    assert (await client.receive_json())["error"]["code"] == "not_found"
    await settled(hass, entry)
    assert len(fake.reads_of()) == reads  # read once, not kept up to date
    assert all(key not in hub.listened() for key in members)


async def test_a_reload_tells_the_panel_and_keeps_values_marked(hass, fake, tmp_path, hass_ws_client):
    entry = await _loaded(hass, fake, tmp_path)
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "weishaupt/panel/subscribe", "entry_id": entry.entry_id})
    await client.receive_json()
    await client.receive_json()
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    import asyncio
    while True:
        event = (await asyncio.wait_for(client.receive_json(), 5))["event"]
        if event.get("reloaded"):
            break
    # the new hub: values kept across the reload, marked until read again
    hub = entry.runtime_data
    kept = next(iter(hub.restored), None)
    if kept is not None:
        assert panel._reading(hub, kept)["kept"] is True


async def test_definitions_name_real_entities_and_messages_not_read(hass, fake, tmp_path):
    entry = await _loaded(hass, fake, tmp_path)
    hub = entry.runtime_data
    hub.named_entities.add(f"{entry.entry_id}_bc1/DHWTemp/value")
    definitions = panel.tree(hass, hub)["definitions"]
    assert [e["entity_id"] for e in definitions["named_from_metadata"]][0].startswith("sensor.boiler_1")
    reasons = {m["key"]: m["reason"] for m in definitions["not_usable"]}
    assert reasons["broadcast/Datetime"] == "write_only"
    readable = definitions["usable"] + sum(1 for r in reasons.values() if r in ("mismatch", "other"))
    assert readable == definitions["usable"]  # the bench: every readable message is loaded


async def test_read_now_counts_what_it_requests_and_what_waits_ahead(hass, fake, tmp_path):
    """Before the first pass ends, a Read now waits behind the reads still due; what an entity already reads is
    not counted."""
    from custom_components.weishaupt.panel import _estimate
    entry = make_entry(hass, fake, gap=0.0)
    await setup(hass, entry)
    hub = entry.runtime_data
    members = hub.model.groups["fs2/heating1"].members
    listened = next(iter(hub.listened()))
    assert hub.to_read_once([*members, listened]) == list(members)  # the listened one is not counted
    state = {"ahead": 95, "first_pass": True, "gap": 2.0}
    assert _estimate(21, state) == {"queued": 21, "seconds": 42, "ahead": 95, "wait": 190, "first_pass": True}
    await settled(hass, entry)
    assert hub.queue_state()["first_pass"] is False and hub.queue_state()["ahead"] == 0


async def test_the_card_finds_the_day_texts_of_a_program_sensor(hass, fake, tmp_path, entity_registry_enabled_by_default):
    """The card maps a program sensor to its day texts by device and translation key (`<sensor's key>_<day>`):
    the registry the frontend sees must hold exactly that."""
    from homeassistant.helpers import entity_registry as er
    from custom_components.weishaupt.const import DOMAIN
    entry = await _loaded(hass, fake, tmp_path)
    registry = er.async_get(hass)
    sensor = registry.async_get(registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_fs1/group/heating1"))
    texts = [e for e in er.async_entries_for_config_entry(registry, entry.entry_id)
             if e.domain == "text" and e.device_id == sensor.device_id
             and e.translation_key and e.translation_key.startswith(f"{sensor.translation_key}_")]
    assert sorted(e.translation_key.rsplit("_", 1)[1] for e in texts) == sorted(
        ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])


async def test_panel_rows_carry_the_codes(hass, fake, tmp_path):
    """Each row carries the vendor codes of its value with the label and document of their scheme."""
    entry = await _loaded(hass, fake, tmp_path)
    tree = panel.tree(hass, entry.runtime_data)
    rows = {row["key"]: row for d in tree["devices"] for row in d["rows"]}
    assert rows["fs1/RoomNormalTemp/value"]["vendor_codes"] == [{
        "code": "P112", "scheme": "wcm-fs-2", "document": "83277504",
        "scheme_label": {"en": "WCM-FS 2.0 room unit and WCM-EM 2.1 module",
                         "fr": "Commande à distance WCM-FS 2.0 et module WCM-EM 2.1"}}]
    assert [c["code"] for c in rows["bc1/Counters/burnerhours"]["vendor_codes"]] == ["i43"]
    assert rows["bc1/Counters/operatinghours"]["vendor_codes"] == []
    coded = sum(1 for row in rows.values() if row["vendor_codes"])
    assert coded > 100


async def test_panel_rows_without_codes_in_the_metadata(hass, fake, tmp_path):
    """A metadata without codes (before definitions 1.4.0) beside the configuration: rows with an empty list."""
    data = _without_codes(json.loads(METADATA_FILE.read_text()))
    data["definitions"]["version"] = "1.4.1"
    folder = Path(hass.config.path("weishaupt"))
    folder.mkdir(exist_ok=True)
    text = json.dumps(data).encode()
    (folder / "weishaupt-metadata-1.4.1.json").write_bytes(text)
    (folder / "sha256sums-1.4.1.txt").write_text(f"{hashlib.sha256(text).hexdigest()}  weishaupt-metadata-1.4.1.json\n")
    entry = await _loaded(hass, fake, tmp_path)
    assert entry.runtime_data.model.version == "1.4.1"
    tree = panel.tree(hass, entry.runtime_data)
    assert all(row["vendor_codes"] == [] for d in tree["devices"] for row in d["rows"])
