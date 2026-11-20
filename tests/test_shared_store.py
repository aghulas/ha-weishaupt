"""A device that reads a program or a setting from another device's store (room unit 2 from room unit 1): a write
to it is acknowledged and not kept. With the metadata marker `shared_with` (definitions 0.5.15 and later), nothing is
ever written to it, even with write conditions; it is shown read only with where it is changed. Without the marker,
nothing changes: the programs of room unit 2 have no write conditions in the definitions, so are never written."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er

from custom_components.weishaupt import panel
from custom_components.weishaupt.const import DOMAIN
from custom_components.weishaupt.model import METADATA_FILE
from ha_common import make_entry, settled, setup
from test_ha_programs import device_id, log  # noqa: F401  (log is a fixture)


def _metadata_with_shared_store(hass, conditions: bool) -> None:
    """The shipped metadata as 0.5.9 beside the configuration: heating program 1 and the setback temperature of room
    unit 2 marked as kept by room unit 1; with `conditions`, the program's slots also carry write conditions (as if
    a release had marked them writable), which the marker must override."""
    data = copy.deepcopy(json.loads(METADATA_FILE.read_text()))
    data["definitions"]["version"] = "0.5.9"
    messages = data["messages"]
    for key, message in messages.items():
        if key.startswith("fs2/HCProgram1"):
            owner = key.replace("fs2/", "fs1/")
            message["shared_with"] = owner
            if conditions:
                message["write"] = copy.deepcopy(messages[owner]["write"])
    messages["fs2/RoomSetbackTemp"]["shared_with"] = "fs1/RoomSetbackTemp"
    folder = Path(hass.config.path("weishaupt"))
    folder.mkdir(exist_ok=True)
    text = json.dumps(data).encode()
    (folder / "weishaupt-metadata-0.5.9.json").write_bytes(text)
    (folder / "sha256sums-0.5.9.txt").write_text(f"{hashlib.sha256(text).hexdigest()}  weishaupt-metadata-0.5.9.json\n")


async def test_a_shared_program_is_never_written_and_says_where_to_change_it(hass, fake, log,
                                                                              entity_registry_enabled_by_default):
    _metadata_with_shared_store(hass, conditions=True)
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    hub = entry.runtime_data
    writer = hub.writer
    assert hub.model.version == "0.5.9"
    # not offered, whatever its write conditions
    assert "fs2/heating1" not in writer.programs and "fs1/heating1" in writer.programs
    assert not any(key.startswith("fs2/HCProgram1") for key in writer.slot_specs)
    registry = er.async_get(hass)
    assert registry.async_get_entity_id("text", DOMAIN, f"{entry.entry_id}_fs2/heating1/monday") is None
    # the action refuses with a translated message naming the device to change it on
    writer.set_switch(True)
    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(DOMAIN, "set_program", {
            "device_id": device_id(hass, entry, "room2"), "program": "heating1", "monday": "06:00-07:00"},
            blocking=True)
    assert err.value.translation_key == "program_shared"
    assert err.value.translation_placeholders["device"] == "Room unit 1"
    assert fake.writes == []
    # the panel and the program sensor say where it is changed
    await settled(hass, entry)
    room2 = next(d for d in panel.tree(hass, hub)["devices"] if d["id"] == "room2")
    program = next(p for p in room2["programs"] if p["key"] == "fs2/heating1")
    assert program["writable"] is False and program["edited_on"]["key"] == "fs1/heating1"
    sensor = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_fs2/group/heating1")
    assert hass.states.get(sensor).attributes["edited_on"] == "Room unit 1"


async def test_a_shared_setting_is_not_offered(hass, fake, log):
    _metadata_with_shared_store(hass, conditions=False)
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    writer = entry.runtime_data.writer
    assert "fs2/RoomSetbackTemp" not in writer.specs and "fs1/RoomSetbackTemp" in writer.specs
    assert writer.not_writable["fs2/RoomSetbackTemp"] == "kept by fs1/RoomSetbackTemp: changed there"
    assert er.async_get(hass).async_get_entity_id("number", DOMAIN,
                                                  f"{entry.entry_id}_fs2/RoomSetbackTemp/value") is None
    row = next(r for d in panel.tree(hass, entry.runtime_data)["devices"] if d["id"] == "room2"
               for r in d["rows"] if r["message"] == "fs2/RoomSetbackTemp")
    assert row["edited_on"]["key"] == "fs1/RoomSetbackTemp"


async def test_without_the_marker_room_unit_2_programs_stay_read_only(hass, fake, log):
    """The shipped definitions give room unit 2's programs no write conditions: never offered, no pointer."""
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    hub = entry.runtime_data
    assert not any(key.startswith("fs2/") for key in hub.writer.programs)
    room2 = next(d for d in panel.tree(hass, hub)["devices"] if d["id"] == "room2")
    assert all(not p["writable"] and p["edited_on"] is None for p in room2["programs"])
