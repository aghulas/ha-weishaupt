"""Fault numbers on the entities (definitions 1.6.0 and later): the state stays the number, the attributes
`fault_code` and `fault` say what the code list of the definitions makes of it, in the language of Home Assistant;
nothing for 0, a number in no list, or a metadata without lists."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from custom_components.weishaupt.model import METADATA_FILE
from ha_common import make_entry, settled, setup, state_of
from test_fault_codes import _without_lists

FAULT = ("fault_code", "fault")


async def test_a_pending_fault_with_its_code_and_label(hass, fake, entity_registry_enabled_by_default):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    hub = entry.runtime_data
    pending = state_of(hass, entry, "ka/ErrorStatus/value")
    assert pending.state == "0" and not set(FAULT) & set(pending.attributes)  # 0: no fault pending
    hub.store("ka/ErrorStatus", ("36",))
    await hass.async_block_till_done()
    pending = state_of(hass, entry, "ka/ErrorStatus/value")
    assert pending.state == "36"  # the raw number stays the state
    assert (pending.attributes["fault_code"], pending.attributes["fault"]) == (
        "F36", "F36 – System water pressure too low")
    hub.store("ka/ErrorStatus", ("15",))  # both a warning and a fault: the system manager stores no letter
    await hass.async_block_till_done()
    assert state_of(hass, entry, "ka/ErrorStatus/value").attributes["fault_code"] == "W15/F15"
    hub.store("em1/ErrorCode", ("181",))  # a code of the WCM list, beside the vendor code of the register
    await hass.async_block_till_done()
    log = state_of(hass, entry, "em1/ErrorCode/value")
    assert log.state == "181" and log.attributes["fault_code"] == "181" and log.attributes["fault"].startswith(
        "181 – ") and log.attributes["vendor_code"]
    hub.store("fs1/ErrorCode", ("99",))  # in no list: the number alone
    await hass.async_block_till_done()
    room = state_of(hass, entry, "fs1/ErrorCode/value")
    assert room.state == "99" and not set(FAULT) & set(room.attributes)


async def test_labels_follow_the_language_of_the_server(hass, fake, entity_registry_enabled_by_default):
    hass.config.language = "fr"
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    entry.runtime_data.store("ka/ErrorStatus", ("36",))
    await hass.async_block_till_done()
    assert state_of(hass, entry, "ka/ErrorStatus/value").attributes["fault"] == (
        "F36 – Pression de l'installation trop faible")
    history = state_of(hass, entry, "bc2/group/fault_history")
    assert history.state == "F36" and history.attributes["fault"] == "F36 – Pression de l'installation trop faible"
    assert history.attributes["entries"][0]["label"] == "Pression de l'installation trop faible"


async def test_without_lists_in_the_metadata_nothing_changes(hass, fake, entity_registry_enabled_by_default):
    """A metadata without code lists (1.5.0 and older) beside the configuration: numbers only."""
    data = _without_lists(json.loads(METADATA_FILE.read_text()))
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
    entry.runtime_data.store("ka/ErrorStatus", ("36",))
    await hass.async_block_till_done()
    pending = state_of(hass, entry, "ka/ErrorStatus/value")
    assert pending.state == "36" and not set(FAULT) & set(pending.attributes)
    history = state_of(hass, entry, "bc1/group/fault_history")
    assert history.state == "W12" and "fault" not in history.attributes
    assert all("label" not in e for e in history.attributes["entries"])
