"""The panel's reads on demand (a menu, a device, the installation: a cost first, then a job followed and stoppable)
and following entities from the panel (enable or disable a row's sensor, all in one go). Reads only, administrators
only; nothing written to the bus."""
from __future__ import annotations

import asyncio

from homeassistant.helpers import entity_registry as er

from custom_components.weishaupt import panel
from custom_components.weishaupt.const import DOMAIN
from ha_common import make_entry, settled, setup, wait_until


async def _loaded(hass, fake, gap: float | None = None):
    """Set up and settled at no gap; then, for a test about pacing, the gap the reader keeps from now on."""
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    if gap is not None:
        entry.runtime_data.request_gap = gap
    return entry


async def _next_event(client, condition, timeout: float = 10.0) -> dict:
    while True:
        event = (await asyncio.wait_for(client.receive_json(), timeout))["event"]
        if condition(event):
            return event


async def test_a_menu_is_priced_then_read_once_and_followed(hass, fake, hass_ws_client):
    entry = await _loaded(hass, fake)
    hub = entry.runtime_data
    keys = panel.scope_keys(hub, "module2", "settings")
    assert keys and not set(keys) & hub.listened()
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "weishaupt/panel/subscribe", "entry_id": entry.entry_id})
    assert (await client.receive_json())["success"]
    first = (await client.receive_json())["event"]
    assert first["jobs"] == {}
    asked = len(fake.reads_of())
    # the cost first: nothing is queued, nothing asked
    await client.send_json({"id": 2, "type": "weishaupt/panel/read_rows", "entry_id": entry.entry_id,
                            "device": "module2", "menu": "settings"})
    price = (await client.receive_json())["result"]
    assert price["queued"] == len(keys) and price["seconds"] == len(keys) * 1 and "job" not in price
    await asyncio.sleep(0.2)
    assert len(fake.reads_of()) == asked and not hub.read_jobs
    # then the reads, followed to their end
    await client.send_json({"id": 3, "type": "weishaupt/panel/read_rows", "entry_id": entry.entry_id,
                            "device": "module2", "menu": "settings", "start": True})
    answer = (await client.receive_json())["result"]
    job = answer["job"]["id"]
    assert answer["job"]["total"] == len(keys)
    end = await _next_event(client, lambda e: e.get("jobs", {}).get(job, {}).get("ended"))
    progress = end["jobs"][job]
    assert progress["done"] == progress["read"] == len(keys) and progress["stopped"] == 0
    reading = panel._reading(hub, keys[0])
    assert reading["once"] is True  # read once, not kept up to date
    commands = [c for _, c in fake.reads_of()][asked:]
    assert len(commands) == len(keys) and all(c.split()[-1] in {k.split("/")[1] for k in keys} for c in commands)
    assert not hub._once and not hub.listened() & set(keys)
    # asked again later, the same rows are read again: still no entity keeps them up to date
    assert panel.scope_keys(hub, "module2", "settings") == keys


async def test_a_read_of_the_installation_can_be_stopped(hass, fake, hass_ws_client):
    entry = await _loaded(hass, fake, gap=5.0)
    hub = entry.runtime_data
    everything = panel.scope_keys(hub)
    assert len(everything) > 100
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "weishaupt/panel/read_rows", "entry_id": entry.entry_id,
                            "start": True})
    answer = (await client.receive_json())["result"]
    assert answer["queued"] == len(everything) and answer["seconds"] == len(everything) * 5
    assert answer["queued"] < 400  # the installation: some ten minutes at the default 2 s
    job = answer["job"]["id"]
    await client.send_json({"id": 2, "type": "weishaupt/panel/stop_read", "entry_id": entry.entry_id, "job": job})
    stopped = (await client.receive_json())["result"]
    assert stopped["ended"] and stopped["stopped"] >= len(everything) - 1
    assert stopped["done"] + stopped["stopped"] == len(everything)
    assert not hub._once
    asked = len(fake.reads_of())
    await asyncio.sleep(0.3)
    assert len(fake.reads_of()) <= asked + 1  # at most the request already under way
    await client.send_json({"id": 3, "type": "weishaupt/panel/stop_read", "entry_id": entry.entry_id, "job": "nope"})
    assert (await client.receive_json())["error"]["code"] == "not_found"


async def test_a_stop_withdraws_only_its_own_reads(hass, fake):
    entry = await _loaded(hass, fake, gap=5.0)
    hub = entry.runtime_data
    program = hub.model.groups["fs2/heating1"].members
    hub.async_read_once(program)  # Read now of a program, before
    job = hub.async_read_job(panel.scope_keys(hub, "room2"))
    assert not set(job.keys) & set(program)
    hub.async_stop_job(job.id)
    assert set(program) <= hub._once  # the program's reads stay queued


async def test_scope_and_errors(hass, fake, hass_ws_client):
    entry = await _loaded(hass, fake)
    client = await hass_ws_client(hass)
    for i, message in enumerate(({"device": "nope"}, {"menu": "settings"}), 1):
        await client.send_json({"id": i, "type": "weishaupt/panel/read_rows", "entry_id": entry.entry_id, **message})
        assert (await client.receive_json())["error"]["code"] == "not_found"
    hub = entry.runtime_data
    # a device is the union of its menus; the installation, of its devices
    device = set(panel.scope_keys(hub, "room1"))
    menus = {m["id"] for d in panel.tree(hass, hub)["devices"] if d["id"] == "room1" for m in d["menus"]}
    assert device == {k for menu in menus for k in panel.scope_keys(hub, "room1", menu)}
    assert set(panel.scope_keys(hub)) == {k for d in hub.devices for k in panel.scope_keys(hub, d)}
    # nothing an enabled entity reads, no program slot
    assert not set(panel.scope_keys(hub)) & hub.listened()
    assert not [k for k in panel.scope_keys(hub) if hub.model.messages[k].family == "program"]


async def test_commands_are_for_administrators(hass, fake, hass_ws_client, hass_read_only_access_token):
    entry = await _loaded(hass, fake)
    client = await hass_ws_client(hass, hass_read_only_access_token)
    for i, message in enumerate(({"type": "weishaupt/panel/read_rows", "start": True},
                                 {"type": "weishaupt/panel/stop_read", "job": "read1"},
                                 {"type": "weishaupt/panel/follow", "enable": ["sensor.x"]}), 1):
        await client.send_json({"id": i, "entry_id": entry.entry_id, **message})
        answer = await client.receive_json()
        assert not answer["success"] and answer["error"]["code"] == "unauthorized"
    assert not entry.runtime_data.read_jobs


async def test_follow_enables_and_disables_in_one_go(hass, fake, hass_ws_client):
    entry = await _loaded(hass, fake)
    hub = entry.runtime_data
    registry = er.async_get(hass)
    tree = panel.tree(hass, hub)
    rows = {r["key"]: r for d in tree["devices"] for r in d["rows"]}
    setting = rows["ka/BlockingTime/value"]["follow"]
    live = rows["bc1/SupplyTemp/value"]["follow"]
    assert setting["enabled"] is False and setting["default"] is False and not setting["blocked"]
    assert live["enabled"] is True and live["default"] is True
    assert rows["bc1/SupplyTemp/value"]["listened"] and not rows["ka/BlockingTime/value"]["listened"]
    program = next(p for d in tree["devices"] for p in d["programs"] if p["key"] == "fs1/heating1")["follow"]
    assert program["enabled"] is False
    foreign = registry.async_get_or_create("sensor", "other", "x").entity_id
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "weishaupt/panel/follow", "entry_id": entry.entry_id,
                            "enable": [setting["entity_id"], program["entity_id"], foreign],
                            "disable": [live["entity_id"]]})
    answer = (await client.receive_json())["result"]
    assert answer["enabled"] == [setting["entity_id"], program["entity_id"]]
    assert answer["disabled"] == [live["entity_id"]]
    assert answer["refused"] == [{"entity_id": foreign, "reason": "not_followable"}]
    assert answer["reload"] is True and answer["reload_after"] == 30
    assert registry.async_get(setting["entity_id"]).disabled_by is None
    assert registry.async_get(live["entity_id"]).disabled_by is er.RegistryEntryDisabler.USER
    # a disabled entity stops at once: its message is no longer listened to, nothing waits for the reload
    await hass.async_block_till_done()
    assert "bc1/SupplyTemp" not in hub.listened()
    # the same again changes nothing
    await client.send_json({"id": 2, "type": "weishaupt/panel/follow", "entry_id": entry.entry_id,
                            "enable": [setting["entity_id"]], "disable": [live["entity_id"]]})
    again = (await client.receive_json())["result"]
    assert again["enabled"] == again["disabled"] == [] and again["reload"] is False


async def test_an_entity_disabled_by_its_device_is_left_alone(hass, fake, hass_ws_client):
    entry = await _loaded(hass, fake)
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_ka/BlockingTime/value")
    registry.async_update_entity(entity_id, disabled_by=er.RegistryEntryDisabler.DEVICE)
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "weishaupt/panel/follow", "entry_id": entry.entry_id,
                            "enable": [entity_id]})
    answer = (await client.receive_json())["result"]
    assert answer["refused"] == [{"entity_id": entity_id, "reason": "blocked"}] and answer["enabled"] == []


async def test_a_reload_ends_the_reads_and_the_panel_is_told(hass, fake, hass_ws_client):
    entry = await _loaded(hass, fake, gap=5.0)
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "weishaupt/panel/subscribe", "entry_id": entry.entry_id})
    await client.receive_json()
    await client.receive_json()
    await client.send_json({"id": 2, "type": "weishaupt/panel/read_rows", "entry_id": entry.entry_id,
                            "device": "room1", "start": True})
    job = None
    while job is None:
        message = await client.receive_json()
        if message.get("id") == 2:
            job = message["result"]["job"]["id"]
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    await _next_event(client, lambda e: e.get("reloaded"))
    hub = entry.runtime_data
    assert hub.read_jobs == {} and not hub._once  # the new hub reads only what its entities ask
    await client.send_json({"id": 3, "type": "weishaupt/panel/stop_read", "entry_id": entry.entry_id, "job": job})
    assert (await client.receive_json())["error"]["code"] == "not_found"
    await wait_until(lambda: hub.first_pass_done is not None)
