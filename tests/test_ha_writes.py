"""Writes inside a Home Assistant test instance, against the simulated ebusd: entities, risk classes, the guard, the
telegrams sent and the read-back. Nothing here reaches a bus: the simulated ebusd keeps what it would have sent."""
import sqlite3
import time

import pytest
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from pytest_homeassistant_custom_component.common import async_capture_events

from custom_components.weishaupt.const import DOMAIN, EVENT_WRITE
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
    """65 number entities (the 66 settings the definitions prove, one register shared by em1 and ka), the write
    switch, off; the probe of the run-time
    checksum is the only write command at start-up, and it is refused by ebusd before sending."""
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    writer = entry.runtime_data.writer
    registry = er.async_get(hass)
    numbers = [e for e in er.async_entries_for_config_entry(registry, entry.entry_id) if e.domain == "number"]
    assert len(numbers) == 65
    assert {e.unique_id.removeprefix(f"{entry.entry_id}_") for e in numbers if not e.disabled_by} == {
        "em2/RoomNormalTemp/value", "em2/RoomSetbackTemp/value"}  # comfort enabled, regulation created disabled
    assert all(e.entity_category == "config" for e in numbers)
    assert hass.states.get(switch_id(hass, entry)).state == "off"
    assert writer.capability == "present" and writer.not_writable == {}
    writes = [c for _, c in fake.commands if c.startswith("write")]
    spec = writer.specs["ka/BlockingTime"]
    assert writes == [f"write -c weishaupt-probe -h {spec.telegram(0)}",
                      f"write -c weishaupt-probe -h {spec.placeholder_telegram(0, '4c')}"]
    assert fake.writes == []
    # the read side is the one of phase 1: the sensors of the settings stay as they were
    assert len([e for e in er.async_entries_for_config_entry(registry, entry.entry_id)
                if e.domain in ("sensor", "binary_sensor")]) == 346
    await settled(hass, entry)
    number = hass.states.get(number_id(hass, entry, "em2/RoomNormalTemp"))
    assert number.state == "21.5" and number.attributes["min"] == 16 and number.attributes["max"] == 35
    assert number.attributes["step"] == 0.5 and number.attributes["unit_of_measurement"] == "°C"
    assert number.attributes["risk"] == "comfort" and number.attributes["proof"] == "change-observed"


async def test_switch_off_refuses(hass, fake, log):
    entry, writer = await writing(hass, fake, log, switch=False)
    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call("number", "set_value", {
            "entity_id": number_id(hass, entry, "em2/RoomNormalTemp"), "value": 22}, blocking=True)
    assert err.value.translation_key == "writes_disabled"
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


async def test_regulation_setting_needs_a_confirmation(hass, fake, log, entity_registry_enabled_by_default):
    """ka blocking time 1 -> 2: setting it sends nothing and opens a repair; confirming it writes the telegram of
    the write test of 2026-11-17 (`cc 25 00 02 00` from ff)."""
    entry, writer = await writing(hass, fake, log)
    await settled(hass, entry)
    fake.commands.clear()
    entity_id = number_id(hass, entry, "ka/BlockingTime")
    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call("number", "set_value", {"entity_id": entity_id, "value": 2}, blocking=True)
    assert err.value.translation_key == "confirmation_pending"
    assert fake.writes == [] and sent(fake) == []
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
    assert result["description_placeholders"]["requested"] == "2 min"
    assert fake.writes == []  # nothing before the confirmation
    result = await manager.async_configure(result["flow_id"], {})
    assert result["type"] == "create_entry"
    assert fake.writes == [("ff", "ka", "15502305cc25000200")]
    assert hass.states.get(entity_id).state == "2.0"
    assert not [i for i in ir.async_get(hass).issues.values() if i.translation_key == "confirm_write"]


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
    assert writes["capability"] == "present" and len(writes["writable"]) == 66
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
