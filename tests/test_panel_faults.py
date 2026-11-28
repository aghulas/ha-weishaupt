"""Fault tables of the panel: the boilers' fault memory with texts, their counters, the system manager's fault-log
entry; read once on demand when no enabled entity reads them. Read only."""
from __future__ import annotations

from custom_components.weishaupt import panel
from ha_common import make_entry, settled, setup, wait_until


async def test_fault_tables_read_once_on_demand(hass, fake, hass_ws_client):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    hub = entry.runtime_data
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "weishaupt/panel/faults", "entry_id": entry.entry_id})
    tables = {t["device"]: t for t in (await client.receive_json())["result"]}
    boiler = tables["boiler1"]
    # the fault memory is read by its sensor (enabled); the counters' entities are disabled: not read
    assert boiler["history"]["entries"] and boiler["not_listened"] > 0
    assert all(c["count"] is None for c in boiler["counters"])
    keys = boiler["keys"]
    assert "bc1/FaultHistorySlot1" in keys and "bc1/FaultHistoryPointer" in keys and "bc1/FaultCounters1" in keys
    asked = len(fake.reads_of())
    await client.send_json({"id": 2, "type": "weishaupt/panel/read_faults", "entry_id": entry.entry_id,
                            "device": "boiler1"})
    answer = (await client.receive_json())["result"]
    # only what is really requested: the messages no enabled entity reads (the fault memory has its sensor)
    assert answer["queued"] == boiler["to_read"] == boiler["not_listened"] < len(keys)
    assert {"seconds", "ahead", "wait", "first_pass"} <= set(answer) and answer["first_pass"] is False
    await wait_until(lambda: all(key in hub.readings for key in keys))
    assert len(fake.reads_of()) - asked == answer["queued"]  # one request each, once
    boiler = {t["device"]: t for t in panel.fault_tables(hub)}["boiler1"]
    entries = boiler["history"]["entries"]
    assert boiler["history"]["ordered"] and entries[0]["slot"] == 6  # pointer 561: slot 6 written last
    assert all(e["code"][0] in "FW" for e in entries) and entries[0]["text"]["en"]
    # the text of an entry is the label of the code list of the definitions (1.6.0 and later)
    assert entries[0]["code"] == "W12" and entries[0]["text"]["fr"] == "Limiteur, départ ou retour au-dessus de 95 °C"
    counter = next(c for c in boiler["counters"] if c["number"] == 57)
    assert counter["count"] == 20 and counter["text"]["fr"]
    await settled(hass, entry)
    assert len(fake.reads_of()) - asked == answer["queued"]  # not kept up to date
    manager = {t["device"]: t for t in panel.fault_tables(hub)}["manager"]
    assert manager["log"] is not None
    await client.send_json({"id": 3, "type": "weishaupt/panel/read_faults", "entry_id": entry.entry_id,
                            "device": "manager"})
    assert (await client.receive_json())["success"]
    await wait_until(lambda: panel.fault_tables(hub)[0] is not None and {
        t["device"]: t for t in panel.fault_tables(hub)}["manager"]["log"]["entry"] is not None)
    entry_log = {t["device"]: t for t in panel.fault_tables(hub)}["manager"]["log"]["entry"]
    assert set(entry_log) == {"id", "code", "type", "device", "time", "fault"}
    assert entry_log["code"] == 0 and entry_log["fault"] is None  # 0: no fault, in no code list


async def test_fault_tables_are_for_administrators(hass, fake, hass_ws_client, hass_read_only_access_token):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    client = await hass_ws_client(hass, hass_read_only_access_token)
    for i, message in enumerate(({"type": "weishaupt/panel/faults"},
                                 {"type": "weishaupt/panel/read_faults", "device": "boiler1"}), 1):
        await client.send_json({"id": i, "entry_id": entry.entry_id, **message})
        answer = await client.receive_json()
        assert not answer["success"] and answer["error"]["code"] == "unauthorized"
    admin = await hass_ws_client(hass)
    await admin.send_json({"id": 9, "type": "weishaupt/panel/read_faults", "entry_id": entry.entry_id,
                           "device": "module2"})  # no fault message (room units have a fault log from 0.5.14)
    assert (await admin.receive_json())["error"]["code"] == "not_found"
