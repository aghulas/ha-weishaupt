"""Vendor codes on the entities and in the panel: attributes only (no name, no entity id changes), the scheme
labelled in the language of Home Assistant, nothing with a metadata that has no codes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from custom_components.weishaupt.model import METADATA_FILE
from ha_common import make_entry, settled, setup, state_of
from test_ha_writes import telegram_log
from test_vendor_codes import _without_codes

CODES = ("vendor_code", "vendor_scheme")


async def test_value_entities_carry_the_code_and_its_scheme(hass, fake, entity_registry_enabled_by_default):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    flow = state_of(hass, entry, "bc1/SupplyTemp/value")
    assert flow.entity_id == "sensor.boiler_1_flow_temperature_i35"  # as before the codes
    assert flow.attributes["friendly_name"] == "Boiler 1 Flow temperature (i35)"
    assert (flow.attributes["vendor_code"], flow.attributes["vendor_scheme"]) == ("i35", "WTC-GB boiler automat")
    # a code of a field: on the entity of that field only
    assert state_of(hass, entry, "bc1/Counters/burnerhours").attributes["vendor_code"] == "i43"
    assert not set(CODES) & set(state_of(hass, entry, "bc1/Counters/operatinghours").attributes)
    room = state_of(hass, entry, "fs1/RoomNormalTemp/value")
    assert (room.attributes["vendor_code"], room.attributes["vendor_scheme"]) == (
        "P112", "WCM-FS 2.0 room unit and WCM-EM 2.1 module")
    assert state_of(hass, entry, "ka/BlockingTime/value").attributes["vendor_code"] == "537"
    assert state_of(hass, entry, "ka/CircWithLegionella/value", "binary_sensor").attributes["vendor_code"] == "582"
    # a sensor not fitted keeps its code beside `no_sensor`
    hub = entry.runtime_data
    hub.store("bc1/DHWTemp", ("-40.0",))
    await hass.async_block_till_done()
    dhw = state_of(hass, entry, "bc1/DHWTemp/value")
    assert dhw.attributes["no_sensor"] is True and dhw.attributes["vendor_code"]


async def test_the_scheme_follows_the_language_of_the_server(hass, fake):
    hass.config.language = "fr"
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    flow = state_of(hass, entry, "bc1/SupplyTemp/value")
    assert flow.entity_id == "sensor.chaudiere_1_temperature_de_depart_i35"
    assert flow.attributes["vendor_scheme"] == "Automate de la chaudière WTC-GB"


async def test_settings_carry_the_code(hass, fake, tmp_path):
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=telegram_log(tmp_path / "t.db"))
    await setup(hass, entry)
    setting = state_of(hass, entry, "fs1/RoomNormalTemp/value", "number")
    assert setting.attributes["vendor_code"] == "P112" and setting.attributes["risk"] == "comfort"
    assert state_of(hass, entry, "ka/DHWLegionellaDay/value", "select").attributes["vendor_code"] == "579"


async def test_without_codes_in_the_metadata_nothing_changes(hass, fake, entity_registry_enabled_by_default):
    """A metadata without codes (before definitions 1.4.0) beside the configuration: no code attribute."""
    data = _without_codes(json.loads(METADATA_FILE.read_text()))
    data["definitions"]["version"] = "1.6.1"
    folder = Path(hass.config.path("weishaupt"))
    folder.mkdir(exist_ok=True)
    text = json.dumps(data).encode()
    (folder / "weishaupt-metadata-1.6.1.json").write_bytes(text)
    (folder / "sha256sums-1.6.1.txt").write_text(f"{hashlib.sha256(text).hexdigest()}  weishaupt-metadata-1.6.1.json\n")
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    assert entry.runtime_data.model.version == "1.6.1"
    flow = state_of(hass, entry, "bc1/SupplyTemp/value")
    assert flow.entity_id == "sensor.boiler_1_flow_temperature_i35"
    assert not set(CODES) & set(flow.attributes)

