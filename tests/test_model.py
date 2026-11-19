"""The model built from the metadata file, and its comparison with what ebusd loaded."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from weishaupt_core.ebusd import parse_definitions, parse_info
from weishaupt_core.model import ON_OFF, Model, single_setting, slug

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(__file__).resolve().parent / "data"


@pytest.fixture(scope="module")
def model():
    return Model.load()


@pytest.fixture
def loaded(golden):
    return {circuit: parse_definitions(text) for circuit, text in golden["definitions"].items()}


def test_model_of_the_release(model):
    assert model.version == "0.5.7"
    assert len(model.messages) == 542
    assert sorted(model.devices) == ["boiler1", "boiler2", "manager", "module2", "module3", "room1", "room2",
                                     "room3", "system"]
    assert {c.circuit for c in model.devices["manager"].circuits} == {"ka", "em1"}


def test_real_ebusd_loaded_what_the_metadata_describes(model, loaded):
    """Every message of the metadata, compared with the release as a real ebusd loaded it: no difference."""
    assert model.compare(set(loaded), loaded) == []


def test_missing_and_different_definitions_are_found(model, fake):
    fake.remove_message("ka/BlockingTime")
    fake.edit_message("bc1/SupplyTemp", ",SIN,10,", ",UIN,10,")
    fake.edit_message("bc1/ReturnTemp", ",SIN,10,", ",SIN,,")
    fake.edit_message("bc1/Counters", "burnerstarts", "starts")
    fake.edit_message("fs1/RoomTemp", "°C", "K")
    fake.edit_message("ka/DHWLoadingPriority", "2=Parallel", "2=Other")
    loaded = {circuit: parse_definitions(text) for circuit, text in fake.definitions.items()}
    found = {m.key: (m.reason, m.detail) for m in model.compare(set(loaded), loaded)}
    assert sorted(found) == ["bc1/Counters", "bc1/ReturnTemp", "bc1/SupplyTemp", "fs1/RoomTemp",
                             "ka/BlockingTime", "ka/DHWLoadingPriority"]
    assert found["ka/BlockingTime"] == ("missing", "")
    assert found["bc1/SupplyTemp"] == ("differs", "value: type UIN, expected SIN")
    assert "divisor" in found["bc1/ReturnTemp"][1] and "unit" in found["fs1/RoomTemp"][1]


def test_a_circuit_ebusd_did_not_load_is_all_missing(model):
    found = model.compare({"bc2"}, {})
    assert len(found) == 26 and {m.reason for m in found} == {"missing"}


def test_present_devices(model, golden):
    info = parse_info(golden["info"])
    slaves = {a.address for a in info.addresses.values() if a.role == "slave" and not a.own}
    assert len(model.present_devices(slaves)) == 9
    assert sorted(model.present_devices({"08", "15"})) == ["boiler1", "manager", "system"]
    assert sorted(model.present_devices({"50"})) == ["manager", "system"]  # the manager's own circuit alone
    assert model.present_devices({"03", "99"}) == {}


def test_entities(model):
    keys = [e.key for e in model.value_entities] + [e.key for e in model.group_entities]
    assert len(keys) == len(set(keys))
    by_key = {e.key: e for e in model.value_entities}
    flow = by_key["bc1/SupplyTemp/value"]
    assert (flow.platform, flow.kind, flow.enabled_default, flow.diagnostic) == ("sensor", "live", True, False)
    assert flow.translation_key == "boiler_supplytemp" and flow.name["en"] == "Flow temperature (i35)"
    flame = by_key["ka/Boiler1Status/flame"]
    assert flame.platform == "binary_sensor" and flame.field.values == ON_OFF
    assert flame.name == {"en": "Boiler 1 status – Flame", "fr": "État de la chaudière 1 – Flamme"}
    phase = by_key["ka/Boiler1Status/operatingphase"]
    assert phase.options["BurnerInOperation"] == "burner_in_operation"
    assert by_key["ka/BlockingTime/value"].diagnostic  # a setting, shown read-only
    assert not by_key["bc1/FaultCounters1/code57"].enabled_default
    # no entity for a guard field, a bit without meaning, a program slot, or a register read twice
    assert not [k for k in keys if k.endswith("/firstbyte") or "/ukn" in k or "HCProgram" in k]
    assert "em1/RoomNormalTemp/value" not in by_key and "ka/RoomNormalTemp/value" in by_key
    groups = {e.key: e for e in model.group_entities}
    assert len(groups) == 19  # 17 weekly programs, 2 fault histories
    assert not groups["fs1/group/heating1"].enabled_default and groups["bc1/group/fault_history"].enabled_default
    assert not by_key["ka/BlockingTime/value"].enabled_default and by_key["bc1/Counters/burnerstarts"].enabled_default
    enabled = [e for e in list(model.value_entities) + list(model.group_entities) if e.enabled_default]
    assert len(enabled) == 156  # of 346: live values, states, operating counters, fault histories


def test_no_written_setting_becomes_anything_else_than_a_sensor(model):
    """The value of a writable setting stays a sensor; the number entity comes on top, with writes enabled."""
    writable = [e for e in model.value_entities if e.message.writable]
    assert len(writable) == 68 and {e.platform for e in writable} == {"sensor", "binary_sensor"}
    assert {e.message.key for e in writable if e.platform == "binary_sensor"} == {"ka/CircWithLegionella"}
    # the date and time broadcast has no read: no sensor
    assert not [e for e in model.value_entities if e.message.key == "broadcast/Datetime"]


def test_one_number_per_writable_register(model):
    """66 writable settings, 65 numbers: the system manager's own circuit (em1, address 50) reads three registers
    of the system manager (ka, 15). Where both are writable (maximum flow temperature) the number of ka is the
    one; where only em1 is (normal and setback room temperature) the number writes through em1 and has the name
    of the sensor of ka."""
    writable = {k for k, m in model.messages.items() if m.writable and single_setting(m) is not None}
    numbers = {n.message.key: n for n in model.number_entities}
    selects = {n.message.key: n for n in model.select_entities}
    assert len(writable) == 71 and len(numbers) == 65 and len(selects) == 5
    assert writable - set(numbers) - set(selects) == {"em1/SupplyMaxTemp"}
    day = selects["ka/DHWLegionellaDay"]
    assert day.options["monday"] == "1" and day.option_labels("fr")["off"] == "Arrêt"
    assert numbers["em1/RoomNormalTemp"].translation_key == "manager_roomnormaltemp"
    assert numbers["ka/SupplyMaxTemp"].translation_key == "manager_supplymaxtemp"


def test_slug():
    assert slug("BurnerInOperation") == "burner_in_operation"
    assert slug("off") == "off" and slug("StandbyCheckFan") == "standby_check_fan"


def test_translations_are_generated_from_the_metadata():
    """translations/*.json are exactly what scripts/vendor_metadata.py generates: no hand edit, no drift."""
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "vendor_metadata.py"), "--check"],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


def test_translations_cover_every_entity(model):
    for language in ("en", "fr"):
        text = json.loads((ROOT / "custom_components/weishaupt/translations" / f"{language}.json").read_text())
        for entity in model.value_entities:
            item = text["entity"][entity.platform][entity.translation_key]
            assert item["name"] == entity.name[language]
            assert set(item.get("state", {})) == set((entity.options or {}).values())
        for device in model.devices:
            assert text["device"][device]["name"]
    english = json.loads((ROOT / "custom_components/weishaupt/translations/en.json").read_text())
    french = json.loads((ROOT / "custom_components/weishaupt/translations/fr.json").read_text())

    def keys(node, prefix=""):
        return {f"{prefix}{k}" if not isinstance(v, dict) else None for k, v in node.items()} | {
            key for k, v in node.items() if isinstance(v, dict) for key in keys(v, f"{prefix}{k}.")}
    assert keys(english) == keys(french)


def test_value_list_labels_come_from_the_metadata(model):
    phase = next(e for e in model.value_entities if e.key == "ka/Boiler1Status/operatingphase")
    assert phase.option_labels("en")["burner_in_operation"] == "Burner in operation"
    assert phase.option_labels("fr")["burner_in_operation"] == "Brûleur en service"
    french = json.loads((ROOT / "custom_components/weishaupt/translations/fr.json").read_text())
    priority = french["entity"]["sensor"]["manager_dhwloadingpriority"]
    assert priority["name"] == "Priorité de la charge ECS"
    assert priority["state"] == {"priority": "Priorité", "sliding": "Mobile", "parallel": "Parallèle"}


def test_renamed_message(model):
    renamed = [e for e in model.value_entities if e.former_key]
    assert [(e.key, e.former_key) for e in renamed] == [
        ("ka/DHWLoadingPriority/value", "ka/DHWOperationMode/value")]
    assert "ka/DHWOperationMode" not in model.messages


def test_fixtures_of_the_release(model, golden):
    """The fixtures file (schema 2): telegrams captured on a bus, for all 536 messages. Each has as many values
    as the metadata has fields, the values the evidence states, and the answer the simulated ebusd replays for a
    message is the text of one of its captured telegrams, as the real ebusd gave it again when recorded."""
    fixtures = json.loads((DATA / "fixtures.json").read_text())
    assert fixtures["schema"] == 2 and fixtures["definitions"]["version"] == model.version
    readings = fixtures["readings"]
    assert len(readings) == 789 and {f"{r['circuit']}/{r['message']}" for r in readings} == {
        k for k, m in model.messages.items() if m.read or m.passive}  # the date and time broadcast has no read
    texts: dict[str, set[str]] = {}
    for reading in readings:
        key = f"{reading['circuit']}/{reading['message']}"
        message = model.messages[key]
        values = reading["text"].split(";")
        assert len(values) == len(message.fields), key
        texts.setdefault(key, set()).add(reading["text"])
        for name, expected in reading["expect"].items():
            text = values[message.field(name).index]
            if expected is None:
                assert text == "-", key
            elif isinstance(expected, (int, float)):
                assert abs(float(text) - expected) < 0.05, key  # the record's precision
            else:
                assert text == expected, key
        if reading.get("case") == "first-byte-not-zero":
            assert values[message.guard.index] != "0"
    assert set(golden["reads"]) == {k for k, m in model.messages.items() if m.read or m.passive}
    for key, text in golden["reads"].items():
        assert text in texts[key], key
    assert golden["reads_not_decoded_here"] == ["ka/DHWSwitchDiff", "ka/DeCoupleMinTemp", "ka/RegulationP"]
