"""The integration inside a Home Assistant test instance, against the simulated ebusd."""
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EntityCategory, STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.helpers import device_registry as dr, entity_registry as er, issue_registry as ir

from custom_components.weishaupt.const import DOMAIN
from ha_common import make_entry, settled, setup, state_of


async def test_entities_enabled_when_created(hass, fake):
    """Live values, states, operating counters and the fault histories; not the settings, the weekly programs
    and the other diagnostics."""
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    enabled = {e.unique_id.removeprefix(f"{entry.entry_id}_") for e in entities if not e.disabled_by}
    assert (len(entities), len(enabled)) == (542, 197)
    assert {"bc1/SupplyTemp/value", "ka/Boiler1Status/flame", "bc1/Counters/burnerstarts",
            "bc1/group/fault_history"} <= enabled
    assert not enabled & {"ka/BlockingTime/value", "fs1/group/heating1", "em1/group/dhw",
                          "bc1/FaultCounters1/code57", "bc1/SoftwareVersionCPU/value"}
    setting = registry.async_get(registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_ka/BlockingTime/value"))
    assert setting.entity_category is EntityCategory.DIAGNOSTIC


async def test_devices_and_entities(hass, fake, entity_registry_enabled_by_default):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    hub = entry.runtime_data
    assert entry.state is ConfigEntryState.LOADED
    assert hub.mismatches == [] and len(hub.usable) == 686
    assert not ir.async_get(hass).issues

    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    names = sorted(d.name for d in devices)
    assert names == ["Boiler 1", "Boiler 2", "Heating module 2", "Heating module 3", "Installation",
                     "Room unit 1", "Room unit 2", "Room unit 3", "System manager", "ebusd"]
    hub_device = next(d for d in devices if d.name == "ebusd")
    assert hub_device.sw_version.startswith("26.1")
    boiler = next(d for d in devices if d.name == "Boiler 1")
    assert (boiler.manufacturer, boiler.model, boiler.sw_version) == ("Weishaupt", "WTC", "11.04")
    assert boiler.via_device_id == hub_device.id

    registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert len(entities) == len(hub.model.value_entities) + len(hub.model.group_entities) + 1 == 542
    assert {e.domain for e in entities} == {"sensor", "binary_sensor"}  # nothing that can be set
    assert len({e.unique_id for e in entities}) == len(entities)

    await settled(hass, entry)
    # live values, decoded by a real ebusd from the bytes of the evidence records
    flow = state_of(hass, entry, "bc1/SupplyTemp/value")
    assert flow.state == "50.0" and flow.attributes["unit_of_measurement"] == "°C"
    assert flow.attributes["device_class"] == "temperature" and flow.attributes["state_class"] == "measurement"
    assert flow.entity_id == "sensor.boiler_1_flow_temperature_i35"
    assert state_of(hass, entry, "bc1/Temperatures/supplytemp").state == "63"
    assert state_of(hass, entry, "bc1/Operation/load").state == "0"
    assert state_of(hass, entry, "bc1/Operation/ionisation").state == "0.0"
    hours = state_of(hass, entry, "bc1/Counters/operatinghours")
    assert hours.state == "87175" and hours.attributes["state_class"] == "total_increasing"
    assert state_of(hass, entry, "bc1/BurnerServiceHours/value").state == "440"
    # settings, read-only
    assert state_of(hass, entry, "ka/BlockingTime/value").state == "1"
    assert state_of(hass, entry, "ka/DHWSwitchDiff/value").attributes["device_class"] == "temperature_delta"
    mode = state_of(hass, entry, "ka/DHWLoadingPriority/value")
    assert mode.state == "priority" and mode.attributes["options"] == ["priority", "sliding", "parallel"]
    # passive messages, from ebusd's cache
    assert state_of(hass, entry, "ka/Boiler1Status/operatingphase").state == "burner_in_operation"
    assert state_of(hass, entry, "ka/Boiler1Status/flame", "binary_sensor").state == STATE_ON
    assert state_of(hass, entry, "ka/Boiler2Status/flame", "binary_sensor").state == STATE_OFF
    assert state_of(hass, entry, "ka/Boiler1Power/currentload").state == "54"
    assert state_of(hass, entry, "broadcast/KaStatus/dhwtemp").state == "25.5"
    # the replacement value of ebusd ("-") is no value
    assert state_of(hass, entry, "ka/Boiler2Status/outsidetemp").state == STATE_UNKNOWN
    assert state_of(hass, entry, "em1/HcMode/dhw", "binary_sensor").state == STATE_ON
    # a heating module without outside sensor: the message decodes since 0.5.0, the sensor reads the value the
    # module gives for "not fitted", which the definitions mark (0.5.12 and later): unknown, no sensor
    assert state_of(hass, entry, "em2/HcMode/supplyhctemp").state == "25.0"
    outside = state_of(hass, entry, "em2/HcMode/outsidetemp")
    assert outside.state == "unknown" and outside.attributes["no_sensor"] is True


async def test_first_byte_guard(hass, fake, entity_registry_enabled_by_default):
    """A memory read whose first byte is not 0 carries no valid value (notice of the definitions release). The
    invalid answers are the two captured on a bus, from the fixtures file."""
    import json
    from pathlib import Path
    readings = json.loads((Path(__file__).parent / "data" / "fixtures.json").read_text())["readings"]
    invalid = {f"{r['circuit']}/{r['message']}": r["text"] for r in readings
               if r.get("case") == "first-byte-not-zero"}
    assert invalid == {"bc1/FaultCounters6": "10;0;0;0;0;0", "bc1/FaultCounters7": "6;0;0;0"}
    valid = fake.reads["bc1/FaultCounters6"]
    fake.reads.update(invalid)
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    hub = entry.runtime_data
    await settled(hass, entry)
    # the counters read 0 in the invalid answer although they are not: no value is shown
    assert state_of(hass, entry, "bc1/FaultCounters6/code22").state == STATE_UNKNOWN
    assert "bc1/FaultCounters6" not in hub.readings and "bc1/FaultCounters7" not in hub.readings
    assert hub.statistics.invalid_by_message == {"bc1/FaultCounters6": 1, "bc1/FaultCounters7": 1}
    assert state_of(hass, entry, "bc1/FaultCounters5/code32").state != STATE_UNKNOWN
    fake.reads["bc1/FaultCounters6"] = valid
    await hub._read(hub.model.messages["bc1/FaultCounters6"])
    assert valid == "0;17;24;0;0;1" and state_of(hass, entry, "bc1/FaultCounters6/code22").state == "17"
    # a later invalid reading does not replace a valid value
    fake.reads["bc1/FaultCounters6"] = invalid["bc1/FaultCounters6"]
    await hub._read(hub.model.messages["bc1/FaultCounters6"])
    assert state_of(hass, entry, "bc1/FaultCounters6/code22").state == "17"
    assert hub.statistics.invalid_first_byte == 3


async def test_entity_of_a_renamed_message_keeps_its_registry_entry(hass, fake):
    """`DHWOperationMode` became `DHWLoadingPriority` in definitions 0.5.0: an entity created under the former
    name keeps its entity id (and so its history and the user's settings) and gets the new unique id."""
    entry = make_entry(hass, fake)
    registry = er.async_get(hass)
    old = registry.async_get_or_create(
        "sensor", DOMAIN, f"{entry.entry_id}_ka/DHWOperationMode/value", config_entry=entry,
        suggested_object_id="system_manager_hot_water_operating_mode")
    await setup(hass, entry)
    await settled(hass, entry)
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_ka/DHWOperationMode/value") is None
    new = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_ka/DHWLoadingPriority/value")
    assert new == old.entity_id == "sensor.system_manager_hot_water_operating_mode"
    state = hass.states.get(new)  # the user had it enabled: it stays enabled and is read
    assert state.state == "priority" and state.attributes["friendly_name"].endswith("Hot water loading priority")


async def test_weekly_program_and_fault_history(hass, fake, monkeypatch, entity_registry_enabled_by_default):
    import datetime
    from custom_components.weishaupt import sensor
    # a Tuesday (freezing the clock would also freeze the reader, which runs on real time)
    monkeypatch.setattr(sensor.dt_util, "now", lambda: datetime.datetime(2026, 11, 17, 12, 0))
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    program = state_of(hass, entry, "fs1/group/heating1")
    assert program.state == "06:30-22:30"
    assert program.attributes["monday"] == "06:30-18:00" and program.attributes["wednesday"] == "-"
    assert program.attributes["friendly_name"] == "Room unit 1 Heating program 1"
    faults = state_of(hass, entry, "bc1/group/fault_history")
    assert faults.state == "W12" and faults.attributes["ordered"] is True
    entries = faults.attributes["entries"]
    # the pointer reads 0x0231: slot 6 is the most recent entry, as the vendor tool lists them
    assert [e["slot"] for e in entries] == [6, 5, 4, 3, 2, 1]
    assert [e["code"] for e in entries] == ["W12", "F11", "W12", "W12", "W12", "W12"]
    assert entries[0] == {"slot": 6, "code": "W12", "operatingphase": "PostPurge", "load": 44, "pumpspeed": 100,
                          "boilertemp": 94, "fluegastemp": 49, "ionisation": 0.0, "returntemp": 40}
    # the per-slot messages have no entity of their own
    registry = er.async_get(hass)
    assert not [e for e in er.async_entries_for_config_entry(registry, entry.entry_id) if "Slot" in e.unique_id]


async def test_french_server(hass, fake):
    """Names, and with them entity ids, follow the language of the server; unique ids do not."""
    hass.config.language = "fr"
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    flow = state_of(hass, entry, "bc1/SupplyTemp/value")
    assert flow.attributes["friendly_name"] == "Chaudière 1 Température de départ (i35)"
    assert flow.entity_id == "sensor.chaudiere_1_temperature_de_depart_i35"
    assert flow.state == "50.0"
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert "Manager de cascade" in {d.name for d in devices}


async def test_definitions_mismatch_raises_a_repair_issue(hass, fake):
    fake.remove_message("ka/BlockingTime")
    fake.edit_message("bc1/SupplyTemp", ",SIN,10,", ",UIN,10,")
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    hub = entry.runtime_data
    assert sorted(m.key for m in hub.mismatches) == ["bc1/SupplyTemp", "ka/BlockingTime"]
    issue = ir.async_get(hass).async_get_issue(DOMAIN, f"definitions_mismatch_{entry.entry_id}")
    assert issue is not None and issue.severity is ir.IssueSeverity.WARNING and not issue.is_fixable
    assert issue.translation_placeholders == {
        "count": "2", "missing": "1", "different": "1", "version": "1.3.0", "accepted": ">=0.6.0, <2.0",
        "messages": "bc1/SupplyTemp, ka/BlockingTime"}
    registry = er.async_get(hass)
    # no broken entity for the two messages, the others are there
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_ka/BlockingTime/value") is None
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_bc1/SupplyTemp/value") is None
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_bc1/ReturnTemp/value") is not None
    await settled(hass, entry)
    assert not [c for _, c in fake.reads_of() if "bc1 SupplyTemp" in c]
    # the issue goes when ebusd has the definitions again
    fake.definitions = dict(fake._golden_definitions)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"definitions_mismatch_{entry.entry_id}") is None


async def test_ebusd_with_other_definitions(hass, fake):
    """An ebusd that loaded another configuration for these addresses: an error issue, no bus device entity."""
    for circuit in list(fake.definitions):
        fake.definitions[circuit] = "r,x,Other,,,08,5022,000000,value,s,UIN,,,"
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    issue = ir.async_get(hass).async_get_issue(DOMAIN, f"definitions_mismatch_{entry.entry_id}")
    assert issue.severity is ir.IssueSeverity.ERROR and issue.translation_placeholders["count"] == "686"
    assert er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id) == []
    assert fake.reads_of() == []


async def test_absent_device_and_unknown_slave(hass, fake):
    fake.remove_address("52")
    fake.info += '\naddress 26: slave, scanned "MF=Other;ID=X;SW=0100;HW=0100"'
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    hub = entry.runtime_data
    assert "module3" not in hub.devices and len(hub.devices) == 8
    assert [a.address for a in hub.unknown_slaves] == ["26"]
    names = {d.name for d in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)}
    assert "Heating module 3" not in names and "Heating module 2" in names
    assert not ir.async_get(hass).issues  # an absent device is not a mismatch


async def test_scan_answers_of_a_real_bus(hass, fake):
    """Scan answers as a running ebusd reports them: boilers identify as `W?`, controllers have no hardware
    version (`HW=-`), a slave answers the scan with nothing usable (`MF=-;ID=??`), another has no definitions file.
    Neither of the last two gets a device or raises an issue."""
    lines = []
    for line in fake.info.splitlines():
        if line.startswith(("address 08:", "address 18:")):
            line = line.replace("ID=W;", "ID=W?;").replace("HW=0102", "HW=0501")
        elif "scanned" in line:
            line = line.replace("ID=W;", "ID=W ;").replace("HW=0102", "HW=-")
        lines.append(line)
    lines += ['address 07: master #16', 'address 0c: slave #16, scanned "MF=-;ID=??;SW=-;HW=-"',
              'address f1: master #10', 'address f6: slave #10, scanned "MF=Kromschroeder;ID=W ;SW=6618;HW=-"']
    fake.info = "\n".join(lines)
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    hub = entry.runtime_data
    assert len(hub.devices) == 9 and hub.mismatches == []
    assert [a.address for a in hub.unknown_slaves] == ["0c", "f6"]
    assert not ir.async_get(hass).issues
    devices = {d.name: d for d in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)}
    assert len(devices) == 10
    assert (devices["Boiler 1"].sw_version, devices["Boiler 1"].hw_version) == ("11.04", "05.01")
    assert (devices["System manager"].sw_version, devices["System manager"].hw_version) == ("11.04", None)


async def test_no_known_device(hass, fake):
    for address in ("08", "15", "18", "35", "50", "51", "52", "75", "f5"):
        fake.remove_address(address)
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    assert entry.state is ConfigEntryState.LOADED
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"no_devices_{entry.entry_id}") is not None
    assert [d.name for d in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)] == ["ebusd"]


async def test_ebusd_unreachable_at_start(hass, fake):
    entry = make_entry(hass, fake)
    await fake.stop()
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_stops_the_reader(hass, fake):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    seen = len(fake.commands)
    fake.reads["ka/Boiler1Power"] = "1;2;3"
    import asyncio
    await asyncio.sleep(0.2)
    assert len(fake.commands) == seen


async def test_diagnostics_hold_nothing_of_the_site(hass, fake):
    from custom_components.weishaupt.diagnostics import async_get_config_entry_diagnostics
    import json
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    data = await async_get_config_entry_diagnostics(hass, entry)
    text = json.dumps(data, default=str)
    assert "127.0.0.1" not in text and str(fake.port) in text  # the host is redacted, the port is not a secret
    assert data["entry"]["data"]["host"] == "**REDACTED**"
    assert data["definitions"]["metadata_version"] == "1.3.0" and data["definitions"]["mismatches"] == []
    assert not [key for key in data["readings"] if "Program" in key or key == "ka/BlockingTime"]  # disabled, not read
    assert data["ebusd"]["commands_sent"]["info"] == 1 and data["ebusd"]["commands_sent"]["find"] == 19
    # ten circuits, the clock, and the write definitions of eight circuits for the probe of the build
    assert data["reader"]["invalid_first_byte"] == 0 and data["reader"]["failed"] == 0
    assert data["readings"]["bc1/Temperatures"] == "0;60;52;63;15"
    assert len(data["ebusd"]["addresses"]) == 17
