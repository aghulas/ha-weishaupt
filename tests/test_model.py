"""The model built from the metadata file, and its comparison with what ebusd loaded."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from weishaupt_core.ebusd import parse_definitions, parse_info
from weishaupt_core.model import ON_OFF, Model, slug

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(__file__).resolve().parent / "data"


@pytest.fixture(scope="module")
def model():
    return Model.load()


@pytest.fixture
def loaded(golden):
    return {circuit: parse_definitions(text) for circuit, text in golden["definitions"].items()}


def test_model_of_the_release(model):
    assert model.version == "0.4.3"
    assert len(model.messages) == 528
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
    fake.edit_message("ka/DHWOperationMode", "2=Parallel", "2=Other")
    loaded = {circuit: parse_definitions(text) for circuit, text in fake.definitions.items()}
    found = {m.key: (m.reason, m.detail) for m in model.compare(set(loaded), loaded)}
    assert sorted(found) == ["bc1/Counters", "bc1/ReturnTemp", "bc1/SupplyTemp", "fs1/RoomTemp",
                             "ka/BlockingTime", "ka/DHWOperationMode"]
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
    assert groups["fs1/group/heating1"].enabled_default and not groups["fs1/group/dhw_stored"].enabled_default


def test_no_written_setting_becomes_anything_else_than_a_sensor(model):
    writable = [e for e in model.value_entities if e.message.writable]
    assert len(writable) == 17 and {e.platform for e in writable} == {"sensor"}


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


def test_fixtures_of_the_release_decode_as_recorded(model, golden):
    """The 17 readings of the fixtures asset: the bytes of the evidence, decoded by the real ebusd, give the
    value the evidence record states."""
    readings = json.loads((DATA / "fixtures.json").read_text())["readings"]
    assert len(readings) == 17
    for reading in readings:
        key = f"{reading['circuit']}/{reading['message']}"
        message = model.messages[key]
        values = golden["reads"][key].split(";")
        for name, expected in reading["expect"].items():
            assert float(values[message.field(name).index]) == float(expected), key
