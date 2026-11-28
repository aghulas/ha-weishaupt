"""Writes inside a Home Assistant test instance, against the simulated ebusd: entities, risk classes, the guard, the
telegrams sent and the read-back. Nothing here reaches a bus: the simulated ebusd keeps what it would have sent."""
import sqlite3
import time

import pytest
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from pytest_homeassistant_custom_component.common import async_capture_events

from custom_components.weishaupt.const import DOMAIN, EVENT_CHANGE, EVENT_WRITE
from custom_components.weishaupt.guard import WriteRefused
from custom_components.weishaupt.writer import ConfirmationPending, WriteFailed
from ha_common import make_entry, settled, setup, state_of


def telegram_log(path, ff_age: float | None = None, newest_age: float = 1.0) -> str:
    """A telegram log like the ebusd add-on's: the newest telegram `newest_age` s ago, one from ff `ff_age` s ago."""
    now = time.time()
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE telegram (ts INTEGER, qq INTEGER)")
        db.execute("INSERT INTO telegram VALUES (?, ?)", (int((now - newest_age) * 1e9), 0x10))
        if ff_age is not None:
            db.execute("INSERT INTO telegram VALUES (?, ?)", (int((now - ff_age) * 1e9), 0xFF))
    return str(path)


@pytest.fixture
def log(tmp_path):
    return telegram_log(tmp_path / "telegrams.db")


async def writing(hass, fake, log, switch: bool = True):
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    writer = entry.runtime_data.writer
    if switch:
        await hass.services.async_call("switch", "turn_on", {"entity_id": switch_id(hass, entry)}, blocking=True)
    fake.commands.clear()
    return entry, writer


def switch_id(hass, entry) -> str:
    return er.async_get(hass).async_get_entity_id("switch", DOMAIN, f"{entry.entry_id}_writes")


def number_id(hass, entry, key: str) -> str:
    return er.async_get(hass).async_get_entity_id("number", DOMAIN, f"{entry.entry_id}_{key}/value")


def sent(fake) -> list[str]:
    return [c for _, c in fake.commands if c.startswith("write")]


async def test_entities_when_writes_are_enabled(hass, fake, log):
    """77 number entities (78 settings of one number the definitions prove, one register shared by em1 and ka), the write
    switch, off; the probe of the run-time
    checksum is the only write command at start-up, and it is refused by ebusd before sending."""
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    writer = entry.runtime_data.writer
    registry = er.async_get(hass)
    numbers = [e for e in er.async_entries_for_config_entry(registry, entry.entry_id) if e.domain == "number"]
    assert len(numbers) == 77
    # every number enabled when created: writes are enabled by a decision in the options already
    assert not [e for e in numbers if e.disabled_by]
    assert all(e.entity_category == "config" for e in numbers)
    assert hass.states.get(switch_id(hass, entry)).state == "off"
    assert writer.capability == "present"
    # the programs of room unit 1 and heating program 1 of room unit 3, and the clock, are offered too; nine
    # settings of the room units whose meaning is not established have no range: read only
    assert writer.not_writable == {f"{room}/{name}": "no range" for room in ("fs1", "fs2", "fs3")
                                   for name in ("ControlVariation", "HolidayStartThird", "HolidayEndThird")}
    assert writer.clock_writable
    assert len(writer.programs) == 12 and not [k for k in writer.programs if k.startswith("fs2/")]
    selects = [e for e in er.async_entries_for_config_entry(registry, entry.entry_id) if e.domain == "select"]
    assert len(selects) == 5 and not [e for e in selects if e.disabled_by]
    writes = [c for _, c in fake.commands if c.startswith("write")]
    spec = writer.specs["ka/BlockingTime"]
    assert writes == [f"write -c weishaupt-probe -h {spec.telegram(0)}",
                      f"write -c weishaupt-probe -h {spec.placeholder_telegram(0, '4c')}"]
    assert fake.writes == []
    # the read side is the one of phase 1: the sensors of the settings stay as they were
    assert len([e for e in er.async_entries_for_config_entry(registry, entry.entry_id)
                if e.domain in ("sensor", "binary_sensor")]) == 547
    await settled(hass, entry)
    number = hass.states.get(number_id(hass, entry, "em2/RoomNormalTemp"))
    assert number.state == "21.5" and number.attributes["min"] == 16 and number.attributes["max"] == 35
    assert number.attributes["step"] == 0.5 and number.attributes["unit_of_measurement"] == "°C"
    assert number.attributes["risk"] == "comfort" and number.attributes["proof"] == "change-observed"
    setback = hass.states.get(number_id(hass, entry, "em2/RoomSetbackTemp"))
    assert (setback.attributes["min"], setback.attributes["max"], setback.attributes["bounds_from"]) == (
        10.0, 21.5, "metadata") and "83277702" in setback.attributes["range_source"]


async def test_switch_off_refuses(hass, fake, log):
    entry, writer = await writing(hass, fake, log, switch=False)
    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call("number", "set_value", {
            "entity_id": number_id(hass, entry, "em2/RoomNormalTemp"), "value": 22}, blocking=True)
    assert err.value.translation_key == "switch_off"
    assert sent(fake) == [] and fake.writes == []


async def test_comfort_setting_written_directly(hass, fake, log):
    """em2 normal room temperature 21.5 -> 22.0: the telegram of the telegram log of the installation, from ff,
    read back from the device, shown, logged and announced."""
    entry, writer = await writing(hass, fake, log)
    events = async_capture_events(hass, EVENT_WRITE)
    await hass.services.async_call("number", "set_value", {
        "entity_id": number_id(hass, entry, "em2/RoomNormalTemp"), "value": 22}, blocking=True)
    await hass.async_block_till_done()
    assert fake.writes == [("ff", "em2", "51502305640500dc00")]
    assert sent(fake) == ["write -s ff -c em2 -h 51502305640500dc00"]
    reads = [c for _, c in fake.commands if c.startswith("read -f")]
    assert reads == ["read -f -c em2 RoomNormalTemp", "read -f -c em2 RoomSetbackTemp", "read -f -c em2 RoomNormalTemp"]
    assert hass.states.get(number_id(hass, entry, "em2/RoomNormalTemp")).state == "22.0"
    assert len(events) == 1
    event = events[0].data
    assert (event["key"], event["before"], event["requested"], event["read_back"], event["result"]) == (
        "em2/RoomNormalTemp", 21.5, 22.0, 22.0, "ok")
    assert event["telegram"] == "51502305640500dc00" and event["source"] == "ff" and event["risk"] == "comfort"


async def test_a_change_gives_a_logbook_entry(hass, fake, log):
    """Each change asked by a user gives one logbook entry on its entity: visible without any log setting, unlike
    the info line. Before -> after with the unit, the frame, the result in words."""
    from custom_components.weishaupt.logbook import async_describe_events
    entry, writer = await writing(hass, fake, log)
    changes = async_capture_events(hass, EVENT_CHANGE)
    entity_id = number_id(hass, entry, "em2/RoomNormalTemp")
    await hass.services.async_call("number", "set_value", {"entity_id": entity_id, "value": 22}, blocking=True)
    await hass.async_block_till_done()
    described = {}
    async_describe_events(hass, lambda domain, event_type, describe: described.update({event_type: describe}))
    [first] = (described[EVENT_CHANGE](event) for event in changes)
    assert first["entity_id"] == entity_id and first["name"] == hass.states.get(entity_id).name
    assert first["message"] == "21.5 °C → 22.0 °C (ff51502305640500dc00): read back ok"


async def test_regulation_setting_needs_a_confirmation(hass, fake, log, entity_registry_enabled_by_default):
    """ka blocking time 1 -> 2: setting it sends nothing and is no error; a notification says where to confirm,
    the repair shows the details; confirming it writes the telegram of the write test of 2026-11-17
    (`cc 25 00 02 00` from ff) and ends with what was written and read back."""
    entry, writer = await writing(hass, fake, log)
    await settled(hass, entry)
    fake.commands.clear()
    entity_id = number_id(hass, entry, "ka/BlockingTime")
    await hass.services.async_call("number", "set_value", {"entity_id": entity_id, "value": 2}, blocking=True)
    assert fake.writes == [] and sent(fake) == []
    assert hass.states.get(entity_id).attributes["pending"] == "2 min"
    notifications = [n for n in hass.states.async_all("persistent_notification")] or None
    from homeassistant.components.persistent_notification import _async_get_or_create_notifications
    notes = _async_get_or_create_notifications(hass)
    assert len(notes) == 1 and "/config/repairs" in next(iter(notes.values()))["message"]
    issues = [i for i in ir.async_get(hass).issues.values() if i.translation_key == "confirm_write"]
    assert len(issues) == 1 and issues[0].is_fixable
    placeholders = issues[0].translation_placeholders
    assert (placeholders["current"], placeholders["requested"], placeholders["minimum"], placeholders["maximum"]) == (
        "1 min", "2 min", "0 min", "30 min")
    assert hass.states.get(entity_id).state == "1.0"

    from homeassistant.components.repairs import repairs_flow_manager
    from homeassistant.setup import async_setup_component
    assert await async_setup_component(hass, "repairs", {})
    manager = repairs_flow_manager(hass)
    result = await manager.async_init(DOMAIN, data={"issue_id": issues[0].issue_id})
    assert result["type"] == "form" and result["step_id"] == "confirm"
    shown = result["description_placeholders"]
    assert (shown["requested"], shown["address"], shown["register"], shown["source"], shown["step"]) == (
        "2 min", "15", "25 00", "ff", "1")
    assert shown["source_text"] == "address of the vendor service tool"
    assert fake.writes == []  # nothing before the confirmation
    result = await manager.async_configure(result["flow_id"], {})
    assert result["type"] == "create_entry" and result["description"] == "written"
    # the whole frame, source address first
    assert (result["description_placeholders"]["read_back"], result["description_placeholders"]["telegram"]) == (
        "2 min", "ff15502305cc25000200")
    assert fake.writes == [("ff", "ka", "15502305cc25000200")]
    assert hass.states.get(entity_id).state == "2.0" and hass.states.get(entity_id).attributes["pending"] is None
    assert not [i for i in ir.async_get(hass).issues.values() if i.translation_key == "confirm_write"]
    assert _async_get_or_create_notifications(hass) == {}


async def test_an_automation_cannot_confirm(hass, fake, log):
    """The writer itself never writes a regulation setting unconfirmed, whoever asks."""
    entry, writer = await writing(hass, fake, log)
    with pytest.raises(ConfirmationPending):
        await writer.async_write("ka/BlockingTime", 2, None)
    with pytest.raises(ConfirmationPending):
        await writer.async_request("em2/GradientCurve", 10.5, None)
    assert fake.writes == []
    assert len(writer.pending) == 2  # one per setting; asking again replaces the earlier request
    with pytest.raises(ConfirmationPending):
        await writer.async_request("em2/GradientCurve", 11, None)
    assert len(writer.pending) == 2


async def test_confirmation_expires(hass, fake, log, monkeypatch):
    entry, writer = await writing(hass, fake, log)
    with pytest.raises(ConfirmationPending):
        await writer.async_request("ka/BlockingTime", 2, None)
    pending = next(iter(writer.pending.values()))
    pending.created -= 901
    with pytest.raises(WriteFailed) as err:
        await writer.async_confirm(pending.id, None)
    assert err.value.code == "expired" and fake.writes == []


async def test_source_31(hass, fake, log):
    """The flow limits of the modules are written from ebusd's own address (no -s), as captured."""
    entry, writer = await writing(hass, fake, log)
    with pytest.raises(ConfirmationPending):
        await writer.async_request("em2/SupplyMaxTemp", 75.5, None)
    await writer.async_confirm(next(iter(writer.pending)), None)
    assert sent(fake) == ["write -c em2 -h 51502305fe2800f302"]
    assert fake.writes == [(None, "em2", "51502305fe2800f302")]


async def test_source_31_refused_when_ebusd_has_another_address(hass, fake, log):
    fake.info = fake.info.replace("address 31: master #8, ebusd", "address 31: master #8").replace(
        "address 30: master #3", "address 30: master #3, ebusd")
    entry, writer = await writing(hass, fake, log)
    with pytest.raises(WriteRefused) as err:
        await writer.async_request("em2/SupplyMinTemp", 8.5, None)
    assert err.value.code == "source_not_own" and fake.writes == []


@pytest.mark.parametrize("key,value,code", [
    ("em2/RoomNormalTemp", 35.5, "out_of_bounds"),
    ("em2/RoomNormalTemp", 15.5, "out_of_bounds"),
    ("em2/RoomNormalTemp", 21.7, "off_step"),
    ("em2/RoomSetbackTemp", 22.0, "out_of_bounds"),  # range of the evidence record, 10.0 to 21.5
    ("em2/RoomNormalTemp", 21.0, "out_of_bounds"),  # below the setback temperature (21.5): linked bound
    ("ka/DHWLoadingPriority", 1, "not_writable"),  # no write conditions in the metadata
    ("bc1/BurnerServiceHours", 0, "not_writable"),  # nothing on a boiler
])
async def test_refusals(hass, fake, log, key, value, code):
    entry, writer = await writing(hass, fake, log)
    with pytest.raises(WriteRefused) as err:
        await writer.async_write(key, value, None, confirmed=True)
    assert err.value.code == code
    assert fake.writes == []


async def test_rate_limit_per_register(hass, fake, log):
    entry, writer = await writing(hass, fake, log)
    await writer.async_write("em2/RoomSetbackTemp", 21.0, None)
    with pytest.raises(WriteRefused) as err:
        await writer.async_write("em2/RoomSetbackTemp", 20.5, None)
    assert err.value.code == "register_interval"
    assert fake.writes == [("ff", "em2", "51502305c00800d200")]


@pytest.mark.parametrize("ff_age,newest_age,path,code", [
    (60, 1, True, "service_tool_active"),  # a telegram from ff a minute ago, not ours
    (None, 600, True, "log_stale"),  # the log is no longer fed
    (None, 1, False, "log_unreadable"),  # no log at that path
])
async def test_service_tool_and_telegram_log(hass, fake, tmp_path, ff_age, newest_age, path, code):
    db = telegram_log(tmp_path / "t.db", ff_age, newest_age) if path else str(tmp_path / "none.db")
    entry, writer = await writing(hass, fake, db)
    with pytest.raises(WriteRefused) as err:
        await writer.async_write("em2/RoomSetbackTemp", 21.0, None)
    assert err.value.code == code and fake.writes == []
    # a write from ebusd's own address does not depend on the service tool
    if code == "service_tool_active":
        with pytest.raises(ConfirmationPending):
            await writer.async_request("em2/SupplyMaxTemp", 75.5, None)
        await writer.async_confirm(next(iter(writer.pending)), None)
        assert fake.writes == [(None, "em2", "51502305fe2800f302")]


async def test_capability_absent_on_a_stock_ebusd(hass, fake, log):
    """A stock ebusd: the probe tells; every write is refused before anything is asked of the bus."""
    fake.runtime_checksum = False
    entry, writer = await writing(hass, fake, log)
    assert writer.capability == "absent"
    with pytest.raises(WriteRefused) as err:
        await writer.async_write("em2/RoomSetbackTemp", 21.0, None)
    assert err.value.code == "capability_absent"
    assert sent(fake) == [] and fake.writes == []
    # the number entities exist and show the values; the switch says why nothing can be written
    assert hass.states.get(switch_id(hass, entry)).attributes["run_time_checksum"] == "absent"
    assert hass.states.get(switch_id(hass, entry)).attributes["allow_stock_writes"] is False


async def test_stock_write_allowed_for_non_boiler_with_opt_in(hass, fake, log):
    """A stock ebusd with allow_stock_writes on: a non-boiler setting is written end to end and the telegram
    carries the checksum byte of the definition (its placeholder), the byte the on-site validation saw on the
    bus. The guard and the read-back are unchanged."""
    fake.runtime_checksum = False
    entry = make_entry(hass, fake, writes_enabled=True, allow_stock_writes=True, telegram_db=log)
    await setup(hass, entry)
    writer = entry.runtime_data.writer
    assert writer.capability == "absent" and writer.allow_stock_writes
    assert hass.states.get(switch_id(hass, entry)).attributes["allow_stock_writes"] is True
    await hass.services.async_call("switch", "turn_on", {"entity_id": switch_id(hass, entry)}, blocking=True)
    fake.commands.clear()
    spec = writer.specs["em2/RoomSetbackTemp"]
    placeholder = writer.placeholders["em2/RoomSetbackTemp"]
    expected = spec.placeholder_telegram(21.0, placeholder)
    assert expected != spec.telegram(21.0)  # the placeholder byte, not the run-time checksum
    result = await writer.async_write("em2/RoomSetbackTemp", 21.0, None)
    assert result["result"] == "ok" and result["telegram"] == expected
    assert [c for c in sent(fake)] == [f"write -s ff -c em2 -h {expected}"]
    assert fake.writes == [("ff", "em2", expected)]


async def test_stock_opt_in_never_writes_a_boiler_automat(hass, fake, log):
    """allow_stock_writes relaxes only the non-boiler controllers: a write to a boiler automat (08/18) stays
    refused on a stock ebusd. No boiler setting is writable today, so a hypothetical one is built from an
    existing spec to prove the gate."""
    import dataclasses
    fake.runtime_checksum = False
    entry = make_entry(hass, fake, writes_enabled=True, allow_stock_writes=True, telegram_db=log)
    await setup(hass, entry)
    writer = entry.runtime_data.writer
    writer.set_switch(True)
    assert writer.boiler_addresses == {"08", "18"}
    non_boiler = writer.specs["em2/RoomSetbackTemp"]
    boiler = dataclasses.replace(non_boiler, zz=next(iter(writer.boiler_addresses)))
    assert writer._stock_write_allowed(non_boiler) is True
    assert writer._stock_write_allowed(boiler) is False
    with pytest.raises(WriteRefused) as err:
        writer._check_static(boiler, "bc1/Hypothetical", boiler.minimum)
    assert err.value.code == "capability_absent"


async def test_stock_opt_in_still_refuses_an_unknown_build(hass, fake, log, monkeypatch):
    """allow_stock_writes relaxes only a build proven stock (capability "absent"): an unclassified build
    (capability "unknown") stays refused even with the option on — fail safe."""
    monkeypatch.setattr(fake, "_write", lambda source, circuit, text: "ERR: timeout")
    entry = make_entry(hass, fake, writes_enabled=True, allow_stock_writes=True, telegram_db=log)
    await setup(hass, entry)
    writer = entry.runtime_data.writer
    assert writer.capability == "unknown" and writer.allow_stock_writes
    writer.set_switch(True)
    with pytest.raises(WriteRefused) as err:
        await writer.async_write("em2/RoomSetbackTemp", 21.0, None)
    assert err.value.code == "capability_unknown" and fake.writes == []


async def test_read_back_mismatch(hass, fake, log):
    """The device acknowledges and keeps its value (as a heating module does for a setting sent from 31): the
    read-back says so, the user is told, the event says "not taken"."""
    entry, writer = await writing(hass, fake, log)
    events = async_capture_events(hass, EVENT_WRITE)
    fake.not_taken.add("em2/RoomSetbackTemp")
    with pytest.raises(WriteFailed) as err:
        await writer.async_write("em2/RoomSetbackTemp", 21.0, None)
    assert err.value.code == "not_taken"
    await hass.async_block_till_done()
    assert events[0].data["result"] == "not taken" and events[0].data["read_back"] == 21.5
    # through the entity, the user sees an error
    await hass.services.async_call("switch", "turn_on", {"entity_id": switch_id(hass, entry)}, blocking=True)
    fake.not_taken.add("em2/RoomNormalTemp")
    with pytest.raises(HomeAssistantError) as shown:
        await hass.services.async_call("number", "set_value", {
            "entity_id": number_id(hass, entry, "em2/RoomNormalTemp"), "value": 22}, blocking=True)
    assert shown.value.translation_key == "not_taken"


async def test_unchanged_value_is_not_written(hass, fake, log):
    entry, writer = await writing(hass, fake, log)
    result = await writer.async_write("em2/RoomSetbackTemp", 21.5, None)
    assert result["result"] == "unchanged" and fake.writes == []


async def test_diagnostics_carry_the_writes(hass, fake, log):
    from custom_components.weishaupt.diagnostics import async_get_config_entry_diagnostics
    entry, writer = await writing(hass, fake, log)
    await writer.async_write("em2/RoomSetbackTemp", 21.0, None)
    data = await async_get_config_entry_diagnostics(hass, entry)
    writes = data["writes"]
    assert writes["capability"] == "present" and len(writes["writable"]) == 83
    assert writes["journal"][0]["result"] == "ok" and log not in str(data)


async def test_a_write_ebusd_does_not_send_is_an_error(hass, fake, log, monkeypatch):
    entry, writer = await writing(hass, fake, log)
    events = async_capture_events(hass, EVENT_WRITE)
    monkeypatch.setattr(fake, "_write", lambda source, circuit, text: "ERR: SYN received")
    with pytest.raises(WriteFailed) as err:
        await writer.async_write("em2/RoomSetbackTemp", 21.0, None)
    assert err.value.code == "write_failed"
    await hass.async_block_till_done()
    assert events[0].data["result"] == "not sent"


async def test_no_read_before_no_write(hass, fake, log):
    entry, writer = await writing(hass, fake, log)
    fake.reads.pop("em2/RoomSetbackTemp")
    with pytest.raises(WriteRefused) as err:
        await writer.async_write("em2/RoomSetbackTemp", 21.0, None)
    assert err.value.code == "read_failed" and fake.writes == []


async def test_switch_off_withdraws_the_requests(hass, fake, log):
    entry, writer = await writing(hass, fake, log)
    with pytest.raises(ConfirmationPending):
        await writer.async_request("ka/BlockingTime", 2, None)
    assert [i for i in ir.async_get(hass).issues.values() if i.translation_key == "confirm_write"]
    await hass.services.async_call("switch", "turn_off", {"entity_id": switch_id(hass, entry)}, blocking=True)
    assert writer.pending == {}
    assert not [i for i in ir.async_get(hass).issues.values() if i.translation_key == "confirm_write"]


async def test_confirmation_refused_by_the_guard(hass, fake, tmp_path):
    """The service tool connects between the request and the confirmation: the flow ends refused, nothing sent."""
    db = tmp_path / "t.db"
    entry, writer = await writing(hass, fake, telegram_log(db))
    with pytest.raises(ConfirmationPending):
        await writer.async_request("ka/BlockingTime", 2, None)
    with sqlite3.connect(db) as connection:
        connection.execute("INSERT INTO telegram VALUES (?, ?)", (int(time.time() * 1e9), 0xFF))
    from homeassistant.components.repairs import repairs_flow_manager
    from homeassistant.setup import async_setup_component
    assert await async_setup_component(hass, "repairs", {})
    issue = next(i for i in ir.async_get(hass).issues.values() if i.translation_key == "confirm_write")
    manager = repairs_flow_manager(hass)
    result = await manager.async_init(DOMAIN, data={"issue_id": issue.issue_id})
    result = await manager.async_configure(result["flow_id"], {})
    assert result["type"] == "abort" and result["reason"] == "refused"
    assert "service tool" in result["description_placeholders"]["reason"] and fake.writes == []


async def test_probe_unknown_refuses(hass, fake, log, monkeypatch):
    monkeypatch.setattr(fake, "_write", lambda source, circuit, text: "ERR: timeout")
    entry, writer = await writing(hass, fake, log)
    assert writer.capability == "unknown"
    with pytest.raises(WriteRefused) as err:
        await writer.async_write("em2/RoomSetbackTemp", 21.0, None)
    assert err.value.code == "capability_unknown"


async def test_each_flow_limit_from_the_source_of_its_metadata(hass, fake, log):
    """em1 (the system manager's own circuit) takes its flow limits from ff only; em3 from 31: the write commands
    follow the metadata."""
    entry, writer = await writing(hass, fake, log)
    for key, value in (("em1/SupplyMinTemp", 9.0), ("em3/SupplyMinTemp", 9.0)):
        with pytest.raises(ConfirmationPending):
            await writer.async_request(key, value, None)
        await writer.async_confirm(next(iter(writer.pending)), None)
    em1, em3 = writer.specs["em1/SupplyMinTemp"], writer.specs["em3/SupplyMinTemp"]
    assert sent(fake) == [f"write -s ff -c em1 -h {em1.telegram(9.0)}", f"write -c em3 -h {em3.telegram(9.0)}"]
    assert [w[0] for w in fake.writes] == ["ff", None]


async def test_a_setting_written_through_the_own_circuit_of_the_manager(hass, fake, log,
                                                                       entity_registry_enabled_by_default):
    """The normal room temperature of the system manager is proven written at its own circuit (em1, 50): the
    number has the name of the system manager's sensor and writes through em1."""
    entry, writer = await writing(hass, fake, log)
    entity_id = number_id(hass, entry, "em1/RoomNormalTemp")
    assert entity_id is not None and number_id(hass, entry, "ka/RoomNormalTemp") is None
    assert er.async_get(hass).async_get(entity_id).translation_key == "manager_roomnormaltemp"
    assert number_id(hass, entry, "em1/SupplyMaxTemp") is None and number_id(hass, entry, "ka/SupplyMaxTemp")


async def test_writer_takes_the_hourly_limit_of_the_options(hass, fake, log):
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log, max_writes_per_hour=1)
    await setup(hass, entry)
    writer = entry.runtime_data.writer
    assert writer.guard.max_per_hour == 1
    writer.set_switch(True)
    await writer.async_write("em2/RoomSetbackTemp", 21.0, None)
    with pytest.raises(WriteRefused) as err:
        await writer.async_write("em2/RoomNormalTemp", 22.0, None)
    assert err.value.code == "hourly_limit" and len(fake.writes) == 1


@pytest.mark.parametrize("stored,expected", [(None, 30), (500, 30), ("x", 30), (60, 60)])
async def test_hourly_limit_default_and_a_stored_value_out_of_bounds(hass, fake, log, stored, expected):
    options = {"writes_enabled": True, "telegram_db": log}
    if stored is not None:
        options["max_writes_per_hour"] = stored
    entry = make_entry(hass, fake, **options)
    await setup(hass, entry)
    assert entry.runtime_data.writer.guard.max_per_hour == expected


async def test_values_shown_with_the_decimals_of_the_step(hass, fake, log):
    """8.0 °C, not 8 °C: the frost protection room temperature of room unit 1, as on the installation."""
    entry, writer = await writing(hass, fake, log)
    fake.reads["fs1/RoomFrostProtectionTemp"] = "8.0"
    entry.runtime_data.store("fs1/RoomFrostProtectionTemp", ("8.0",))
    with pytest.raises(ConfirmationPending) as pending:
        await writer.async_request("fs1/RoomFrostProtectionTemp", 8.5, None)
    shown = pending.value.placeholders
    assert (shown["current"], shown["requested"], shown["minimum"], shown["maximum"]) == (
        "8.0 °C", "8.5 °C", "4.0 °C", "16.0 °C")
    assert (shown["address"], shown["register"], shown["source"]) == ("35", "14 0a", "ff")


async def test_the_confirmation_ends_with_what_happened(hass, fake, log):
    """Not taken over, and unchanged: the last dialog says so, with the values."""
    from homeassistant.components.repairs import repairs_flow_manager
    from homeassistant.setup import async_setup_component
    entry, writer = await writing(hass, fake, log)
    assert await async_setup_component(hass, "repairs", {})
    manager = repairs_flow_manager(hass)
    fake.not_taken.add("ka/BlockingTime")
    for value, reason in ((2, "not_taken"), (1, "unchanged")):
        with pytest.raises(ConfirmationPending) as pending:
            await writer.async_request("ka/BlockingTime", value, None)
        result = await manager.async_init(DOMAIN, data={"issue_id": pending.value.issue_id})
        result = await manager.async_configure(result["flow_id"], {})
        if reason == "unchanged":  # nothing to write is no failure
            assert result["type"] == "create_entry" and result["description"] == reason
        else:
            assert result["type"] == "abort" and result["reason"] == reason
        if reason == "not_taken":
            assert result["description_placeholders"]["read_back"] == "1 min"
        await hass.async_block_till_done()
        # a second write of the register within 10 s would be refused: let the guard forget it
        writer.guard._last_by_register.clear()


async def test_number_and_sensor_have_distinct_names(hass, fake, log):
    entry, writer = await writing(hass, fake, log)
    registry = er.async_get(hass)
    number = registry.async_get(number_id(hass, entry, "em2/RoomNormalTemp"))
    assert number.entity_id.endswith("_setting")
    assert hass.states.get(number.entity_id).attributes["friendly_name"].endswith("Normal room temperature (setting)")


async def test_an_entity_just_enabled_is_read_first(hass, fake, log):
    """Enabling an entity reloads the entry; its message is then read before the whole first fill."""
    entry = make_entry(hass, fake, gap=0.05)
    await setup(hass, entry)
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_ka/BlockingTime/value")
    registry.async_update_entity(entity_id, disabled_by=None)
    fake.commands.clear()
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    from ha_common import wait_until
    await wait_until(lambda: any("ka BlockingTime" in c for _, c in fake.reads_of()))
    reads = [c for _, c in fake.reads_of()]
    first = next(i for i, c in enumerate(reads) if "ka BlockingTime" in c)
    before = [c for c in reads[:first] if " -m 30 " not in c and " -m 900 " not in c]
    assert len(before) <= 3, before  # read among the very first requests after the reload, not after ~60 others


async def test_migration_enables_the_numbers_0_3_0b2_disabled(hass, fake, log):
    """0.3.0b2 (entry 2.1) created the regulation numbers disabled by the integration. The migration to 2.2 enables
    those, once, and only those: a number the user disabled, and a sensor disabled when created, stay disabled. The
    numbers it enabled are read first."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from homeassistant.const import CONF_HOST, CONF_PORT
    entry = MockConfigEntry(
        domain=DOMAIN, version=2, minor_version=1, title="Weishaupt", unique_id=f"127.0.0.1:{fake.port}",
        data={CONF_HOST: "127.0.0.1", CONF_PORT: fake.port},
        options={"request_gap": 0.05, "cyclic_interval": 300, "writes_enabled": True, "telegram_db": log})
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    integration, user = er.RegistryEntryDisabler.INTEGRATION, er.RegistryEntryDisabler.USER
    by_integration = registry.async_get_or_create(
        "number", DOMAIN, f"{entry.entry_id}_ka/BlockingTime/value", config_entry=entry, disabled_by=integration)
    by_user = registry.async_get_or_create(
        "number", DOMAIN, f"{entry.entry_id}_ka/ChangeOverTime/value", config_entry=entry, disabled_by=user)
    sensor = registry.async_get_or_create(
        "sensor", DOMAIN, f"{entry.entry_id}_ka/BlockingTime/value", config_entry=entry, disabled_by=integration)
    await setup(hass, entry)
    assert (entry.version, entry.minor_version) == (2, 3)  # and on to 2.3 (endpoints)
    assert registry.async_get(by_integration.entity_id).disabled_by is None
    assert registry.async_get(by_user.entity_id).disabled_by is user
    assert registry.async_get(sensor.entity_id).disabled_by is integration
    from ha_common import wait_until
    await wait_until(lambda: any("ka BlockingTime" in c for _, c in fake.reads_of()))
    reads = [c for _, c in fake.reads_of() if " -m 30 " not in c and " -m 900 " not in c]
    assert "ka BlockingTime" in " ".join(reads[:3])  # among the first requests, not after the first fill
    # a second set-up does not migrate again: the number the user disables later stays disabled
    registry.async_update_entity(by_integration.entity_id, disabled_by=user)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert registry.async_get(by_integration.entity_id).disabled_by is user


async def test_a_reload_keeps_the_values(hass, fake, log):
    """After a reload of the entry (as Home Assistant does when an entity is enabled), the values read before are
    shown at once, and read again in the first pass, so that a change made at the device does not wait for the
    end of their interval."""
    entry, writer = await writing(hass, fake, log)
    await settled(hass, entry)
    fake.reads["em2/RoomNormalTemp"] = "22.0"  # changed at the device while Home Assistant reloads
    before = len(fake.reads_of())
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    entity_id = number_id(hass, entry, "em2/RoomNormalTemp")
    assert hass.states.get(entity_id).state == "21.5"  # the value kept, not unknown
    await settled(hass, entry)
    assert [c for _, c in fake.reads_of()[before:] if "em2 RoomNormalTemp" in c]
    assert hass.states.get(entity_id).state == "22.0" and entry.runtime_data.restored == set()


async def test_a_choice_through_its_confirmation(hass, fake, log):
    """Legionella day of the system manager, Tuesday -> Monday: the telegram captured on the bus (`e8 01 01 01 00`
    from ff), the entries shown by their labels, the whole frame in the result."""
    from homeassistant.components.repairs import repairs_flow_manager
    from homeassistant.setup import async_setup_component
    entry, writer = await writing(hass, fake, log)
    await settled(hass, entry)
    entity_id = er.async_get(hass).async_get_entity_id("select", DOMAIN,
                                                       f"{entry.entry_id}_ka/DHWLegionellaDay/value")
    state = hass.states.get(entity_id)
    assert state.state == "tuesday" and state.attributes["options"][:2] == ["off", "monday"]
    await hass.services.async_call("select", "select_option", {"entity_id": entity_id, "option": "monday"},
                                   blocking=True)
    assert fake.writes == []
    issue = next(i for i in ir.async_get(hass).issues.values() if i.translation_key == "confirm_write")
    shown = issue.translation_placeholders
    assert (shown["current"], shown["requested"]) == ("Tuesday", "Monday")
    assert shown["allowed"] == "Off, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday"
    assert await async_setup_component(hass, "repairs", {})
    manager = repairs_flow_manager(hass)
    result = await manager.async_init(DOMAIN, data={"issue_id": issue.issue_id})
    result = await manager.async_configure(result["flow_id"], {})
    assert result["type"] == "create_entry" and result["description"] == "written"
    assert result["description_placeholders"]["telegram"] == "ff15502305e801010100"
    assert fake.writes == [("ff", "ka", "15502305e801010100")]
    assert hass.states.get(entity_id).state == "monday"


async def test_new_definitions_with_a_reload_only(hass, fake, log):
    """A definitions release placed beside the configuration takes effect at a reload of the entry, without a
    release of the integration: here a narrower range of a setting; removed, the bundled copy is back."""
    import copy
    import hashlib
    import json
    from pathlib import Path
    from custom_components.weishaupt.model import METADATA_FILE
    entry, writer = await writing(hass, fake, log)
    entity_id = number_id(hass, entry, "em2/RoomNormalTemp")
    assert hass.states.get(entity_id).attributes["max"] == 35
    data = copy.deepcopy(json.loads(METADATA_FILE.read_text()))
    data["definitions"]["version"] = "1.6.1"
    data["messages"]["em2/RoomNormalTemp"]["fields"][0]["max"] = 30
    folder = Path(hass.config.path("weishaupt"))
    folder.mkdir(exist_ok=True)
    text = json.dumps(data).encode()
    (folder / "weishaupt-metadata-1.6.1.json").write_bytes(text)
    (folder / "sha256sums-1.6.1.txt").write_text(f"{hashlib.sha256(text).hexdigest()}  weishaupt-metadata-1.6.1.json\n")
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    hub = entry.runtime_data
    assert (hub.metadata_source, hub.model.version) == ("weishaupt-metadata-1.6.1.json", "1.6.1")
    assert hass.states.get(entity_id).attributes["max"] == 30
    assert hub.writer.specs["em2/RoomNormalTemp"].maximum == 30
    assert not [i for i in ir.async_get(hass).issues.values() if i.translation_key == "definitions_file"]
    for file in folder.iterdir():
        file.unlink()
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.metadata_source == "bundled"
    assert hass.states.get(entity_id).attributes["max"] == 35


def _newer_file_with_a_new_message(hass, fake, refused: bool) -> None:
    """A newer metadata file beside the configuration, with a message the shipped translations do not name
    (labelled in English and French), and, if `refused`, a second file with a bad checksum."""
    import copy
    import hashlib
    import json
    from pathlib import Path
    from custom_components.weishaupt.model import METADATA_FILE
    folder = Path(hass.config.path("weishaupt"))
    folder.mkdir(exist_ok=True)
    if refused:
        (folder / "weishaupt-metadata-1.6.2.json").write_text("{}")
        (folder / "sha256sums-1.6.2.txt").write_text("0" * 64 + "  weishaupt-metadata-1.6.2.json\n")
    data = copy.deepcopy(json.loads(METADATA_FILE.read_text()))
    data["definitions"]["version"] = "1.6.1"
    data["messages"]["ka/BlockingTimeCopy"] = dict(copy.deepcopy(data["messages"]["ka/BlockingTime"]),
                                                   name="BlockingTimeCopy")
    data["messages"]["ka/BlockingTimeCopy"].pop("write")
    data["messages"]["ka/BlockingTimeCopy"]["label"] = {"en": "Blocking time copy", "fr": "Copie du temps de blocage"}
    text = json.dumps(data).encode()
    (folder / "weishaupt-metadata-1.6.1.json").write_bytes(text)
    (folder / "sha256sums-1.6.1.txt").write_text(f"{hashlib.sha256(text).hexdigest()}  weishaupt-metadata-1.6.1.json\n")
    line = next(row for row in fake.definitions["ka"].splitlines() if row.split(",")[2] == "BlockingTime")
    fake.definitions["ka"] += "\n" + line.replace(",BlockingTime,", ",BlockingTimeCopy,")


async def test_a_new_message_is_named_from_the_metadata(hass, fake, log, caplog):
    """A newer file with a message the shipped translations do not name: its entity is created with the label of
    the metadata, in the language of Home Assistant. A correct installation has no repair issue; what is in use
    goes to an info line and the diagnostics."""
    import logging
    from custom_components.weishaupt.diagnostics import async_get_config_entry_diagnostics
    caplog.set_level(logging.INFO, logger="custom_components.weishaupt")
    hass.config.language = "fr"
    _newer_file_with_a_new_message(hass, fake, refused=False)
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    hub = entry.runtime_data
    assert hub.model.version == "1.6.1" and hub.metadata_refused == {}
    assert hub.not_named == set() and hub.named_from_metadata == {"sensor.manager_blockingtimecopy"}
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_ka/BlockingTimeCopy/value")
    assert entity_id is not None
    assert er.async_get(hass).async_get(entity_id).original_name == "Copie du temps de blocage"
    # an entity the shipped translations name keeps its translated name
    named = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_ka/BlockingTime/value")
    assert er.async_get(hass).async_get(named).translation_key is not None
    assert not [i for i in ir.async_get(hass).issues.values() if i.translation_key == "definitions_file"]
    line = next(r.getMessage() for r in caplog.records if r.getMessage().startswith("definitions in use"))
    assert line == ("definitions in use: 1.6.1 (weishaupt-metadata-1.6.1.json); 1 entities named from the metadata, "
                    "0 waiting for a name")
    shown = (await async_get_config_entry_diagnostics(hass, entry))["definitions"]
    assert shown["entities_named_from_metadata"] == ["sensor.manager_blockingtimecopy"]
    assert shown["metadata_version"] == "1.6.1" and shown["entities_waiting_for_names"] == []


async def test_a_refused_file_raises_an_issue(hass, fake, log):
    """A file with a bad checksum is not used: a repair issue names it and why; the newer valid file is used."""
    _newer_file_with_a_new_message(hass, fake, refused=True)
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    hub = entry.runtime_data
    assert hub.model.version == "1.6.1", hub.metadata_refused
    assert "weishaupt-metadata-1.6.2.json" in hub.metadata_refused
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_ka/BlockingTimeCopy/value")
    assert er.async_get(hass).async_get(entity_id).original_name == "Blocking time copy"
    issue = next(i for i in ir.async_get(hass).issues.values() if i.translation_key == "definitions_file")
    assert "waiting" not in issue.translation_placeholders
    assert "sha256" in issue.translation_placeholders["refused"] or "schema" in issue.translation_placeholders["refused"]
