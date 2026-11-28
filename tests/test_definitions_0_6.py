"""What definitions 0.6.0 change for an installation that ran 0.5.x: no entity left orphaned, the entity id (and so
the history and the user's settings) kept wherever Home Assistant allows it.

- `em2|em3/MixerPump`: a number (0, 1) becomes the value list off/on, so a binary sensor like every other pump.
  Home Assistant cannot move an entity to another domain: the sensor goes (unless the user customised it), a binary
  sensor comes, with the same object id; the sensor's history stays under its own entity id.
- `ka/LegionellaStartTime`: a number becomes a time of day (TTQ, `08:30`): the same sensor, shown as its text.
- `ka/DHWExceeded` is renamed `ka/DHWExcessTemp`, unit K (a temperature difference): the entity follows the rename.
- A field renamed in the definitions (`renamed_from` on a field, the 18 skip fields of HcMode in 0.6.0): an entity
  of a shown field follows the rename, and an ebusd still loading the former field names is no mismatch."""
from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
from pathlib import Path

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import STATE_OFF
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from custom_components.weishaupt.const import DOMAIN
from custom_components.weishaupt.ebusd import parse_definitions
from custom_components.weishaupt.model import METADATA_FILE, Model
from ha_common import make_entry, settled, setup, state_of


def _former(registry, entry, platform: str, key: str, object_id: str) -> str:
    """An entity as an older version created it, enabled."""
    return registry.async_get_or_create(platform, DOMAIN, f"{entry.entry_id}_{key}", config_entry=entry,
                                        suggested_object_id=object_id).entity_id


async def test_mixer_pump_becomes_a_binary_sensor(hass, fake, entity_registry_enabled_by_default):
    entry = make_entry(hass, fake)
    registry = er.async_get(hass)
    old = _former(registry, entry, "sensor", "em2/MixerPump/value", "heating_module_2_mixer_circuit_pump")
    customised = _former(registry, entry, "sensor", "em3/MixerPump/value", "heating_module_3_mixer_circuit_pump")
    registry.async_update_entity(customised, name="Pump of the floor heating")
    fake.reads["em2/MixerPump"] = "off"  # ebusd gives the name of the value from 0.6.0
    await setup(hass, entry)
    await settled(hass, entry)
    assert registry.async_get(old) is None  # gone, not orphaned
    pump = state_of(hass, entry, "em2/MixerPump/value", platform="binary_sensor")
    assert pump.entity_id == old.replace("sensor.", "binary_sensor.", 1) and pump.state == STATE_OFF
    # a sensor the user customised is kept, with the repair that names it, as for any entity no longer yielded
    assert registry.async_get(customised) is not None
    issue = ir.async_get(hass).async_get_issue(DOMAIN, f"stale_entities_{entry.entry_id}")
    assert issue is not None and customised in issue.translation_placeholders["entities"]


async def test_legionella_start_time_is_shown_as_a_time(hass, fake, entity_registry_enabled_by_default):
    entry = make_entry(hass, fake)
    registry = er.async_get(hass)
    old = _former(registry, entry, "sensor", "ka/LegionellaStartTime/value", "system_manager_legionella_start")
    fake.reads["ka/LegionellaStartTime"] = "08:30"
    await setup(hass, entry)
    await settled(hass, entry)
    state = state_of(hass, entry, "ka/LegionellaStartTime/value")
    assert state.entity_id == old and state.state == "08:30"
    assert "unit_of_measurement" not in state.attributes and "state_class" not in state.attributes


async def test_dhw_excess_temperature_follows_its_rename(hass, fake, entity_registry_enabled_by_default):
    entry = make_entry(hass, fake)
    registry = er.async_get(hass)
    old = _former(registry, entry, "sensor", "ka/DHWExceeded/value", "system_manager_hot_water_exceeded")
    await setup(hass, entry)
    await settled(hass, entry)
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_ka/DHWExceeded/value") is None
    state = state_of(hass, entry, "ka/DHWExcessTemp/value")
    assert state.entity_id == old
    assert state.attributes["unit_of_measurement"] == "K"
    assert state.attributes["device_class"] == SensorDeviceClass.TEMPERATURE_DELTA
    assert float(state.state) == float(fake.reads["ka/DHWExcessTemp"])


def _field_renamed_beside(hass) -> None:
    """The shipped metadata as 0.6.1 beside the configuration, with the flow temperature field of the boiler's
    temperatures renamed `flowtemp`, `renamed_from` the former name (ebusd still has the former one)."""
    data = copy.deepcopy(json.loads(METADATA_FILE.read_text()))
    data["definitions"]["version"] = "1.6.1"
    for fld in data["messages"]["bc1/Temperatures"]["fields"]:
        if fld["name"] == "supplytemp":
            fld.update(name="flowtemp", renamed_from="supplytemp")
    folder = Path(hass.config.path("weishaupt"))
    folder.mkdir(exist_ok=True)
    text = json.dumps(data).encode()
    (folder / "weishaupt-metadata-1.6.1.json").write_bytes(text)
    (folder / "sha256sums-1.6.1.txt").write_text(f"{hashlib.sha256(text).hexdigest()}  weishaupt-metadata-1.6.1.json\n")


async def test_entity_of_a_renamed_field_keeps_its_registry_entry(hass, fake, entity_registry_enabled_by_default):
    _field_renamed_beside(hass)
    entry = make_entry(hass, fake)
    registry = er.async_get(hass)
    old = _former(registry, entry, "sensor", "bc1/Temperatures/supplytemp", "boiler_1_temperatures_flow")
    await setup(hass, entry)
    await settled(hass, entry)
    hub = entry.runtime_data
    assert hub.model.version == "1.6.1" and hub.mismatches == []  # ebusd's former field name is no difference
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_bc1/Temperatures/supplytemp") is None
    state = state_of(hass, entry, "bc1/Temperatures/flowtemp")
    assert state.entity_id == old and state.state == fake.reads["bc1/Temperatures"].split(";")[
        hub.model.messages["bc1/Temperatures"].field("flowtemp").index]


def test_former_key_of_a_field_and_of_a_message():
    model = Model.load()
    hc_mode = model.messages["em1/HcMode"]
    renamed = {f.name: f.renamed_from for f in hc_mode.fields if f.renamed_from}
    assert len(renamed) == 18 and renamed["ukn1_1"] == "ink1_1" and renamed["ukn3_4"] == "opmode_4"
    from custom_components.weishaupt.model import former_key
    fld = hc_mode.field("ukn1_1")
    assert former_key(hc_mode, fld) == "em1/HcMode/ink1_1"
    assert former_key(hc_mode, hc_mode.field("pump")) is None
    excess = model.messages["ka/DHWExcessTemp"]
    assert former_key(excess, excess.fields[0]) == "ka/DHWExceeded/value"
    # both renamed: the former message with the former field
    both = dataclasses.replace(excess, fields=(dataclasses.replace(excess.fields[0], name="delta",
                                                                   renamed_from="value"),))
    assert former_key(both, both.fields[0]) == "ka/DHWExceeded/value"


def test_an_ebusd_still_on_0_5_has_the_former_names_of_hc_mode(golden):
    """ebusd loads 0.5.x (the former skip-field names of HcMode): HcMode is no mismatch. A field name that is
    neither the name nor the former one still is."""
    model = Model.load()
    loaded = {circuit: parse_definitions(text) for circuit, text in golden["definitions"].items()}
    former = {f.name: f.renamed_from for f in model.messages["em1/HcMode"].fields if f.renamed_from}

    def with_names(names):
        out = dict(loaded)
        out["em1"] = [dataclasses.replace(d, fields=tuple(dataclasses.replace(f, name=names.get(f.name, f.name))
                                                          for f in d.fields)) if d.name == "HcMode" else d
                      for d in loaded["em1"]]
        return out
    assert model.compare(set(loaded), with_names(former)) == []
    found = model.compare(set(loaded), with_names({"ukn1_1": "other"}))
    assert [(m.key, m.reason) for m in found] == [("em1/HcMode", "differs")]


async def test_an_ebusd_still_loading_0_5_names_four_messages(hass, fake, entity_registry_enabled_by_default):
    """ebusd still loads definitions 0.5.15 (as a real ebusd does, recorded by scripts/capture_ebusd.py): the
    repair names the four messages 0.6.0 changed in a way ebusd must know (the renamed one is missing, three are
    retyped); HcMode, whose skip fields only changed names, is read; every other entity works."""
    fake.remove_message("ka/DHWExcessTemp")  # ebusd has it as DHWExceeded
    fake.edit_message("ka/LegionellaStartTime", ",TTQ,", ",UIN,")
    for module in ("em2", "em3"):
        fake.edit_message(f"{module}/MixerPump", ",0=off;1=on,", ",,")
    model = Model.load()
    for module in ("em1", "em2", "em3"):
        for fld in model.messages[f"{module}/HcMode"].fields:
            if fld.renamed_from:
                fake.edit_message(f"{module}/HcMode", f",{fld.name},", f",{fld.renamed_from},")
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    hub = entry.runtime_data
    assert sorted((m.key, m.reason) for m in hub.mismatches) == [
        ("em2/MixerPump", "differs"), ("em3/MixerPump", "differs"), ("ka/DHWExcessTemp", "missing"),
        ("ka/LegionellaStartTime", "differs")]
    issue = ir.async_get(hass).async_get_issue(DOMAIN, f"definitions_mismatch_{entry.entry_id}")
    assert issue.severity is ir.IssueSeverity.WARNING and issue.translation_placeholders["accepted"] == ">=0.6.0, <2.0"
    assert state_of(hass, entry, "em2/HcMode/pump", platform="binary_sensor").state in ("on", "off")
    assert er.async_get(hass).async_get_entity_id("binary_sensor", DOMAIN,
                                                  f"{entry.entry_id}_em2/MixerPump/value") is None
