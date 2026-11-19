"""The panel: its WebSocket commands (read only, admin only, nothing asked from the bus) and its registration."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.weishaupt import panel
from ha_common import make_entry, settled, setup
from test_ha_writes import telegram_log


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
    hass.config.components.add("frontend")
    hass.http = MagicMock(async_register_static_paths=AsyncMock())
    with patch("homeassistant.components.panel_custom.async_register_panel", AsyncMock()) as register, \
            patch.object(panel, "PANEL_FILE", built):
        await panel.async_setup_panel(hass, "0.5.0b1")
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
