"""A temperature sensor that is not fitted: the device sends a fixed value (−40.0 °C on a boiler). When the metadata
in use marks the field `absent` with that value (definitions 0.5.12 and later), the entity reads unknown, with the
attribute `no_sensor`; any other value, however close, is shown. Without a marker nothing changes."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from homeassistant.const import STATE_UNKNOWN

from custom_components.weishaupt.model import METADATA_FILE
from ha_common import make_entry, settled, setup, state_of


def _metadata_with_markers(hass) -> None:
    """The shipped metadata as a newer release beside the configuration, with `absent` on two fields of boiler 1."""
    data = copy.deepcopy(json.loads(METADATA_FILE.read_text()))
    data["definitions"]["version"] = "0.5.9"
    for key in ("bc1/DHWTemp", "bc1/HydraulicSeparatorTemp"):
        data["messages"][key]["fields"][0]["absent"] = -40.0
    folder = Path(hass.config.path("weishaupt"))
    folder.mkdir(exist_ok=True)
    text = json.dumps(data).encode()
    (folder / "weishaupt-metadata-0.5.9.json").write_bytes(text)
    (folder / "sha256sums-0.5.9.txt").write_text(f"{hashlib.sha256(text).hexdigest()}  weishaupt-metadata-0.5.9.json\n")


async def test_absent_marker_reads_unknown_only_for_the_exact_value(hass, fake, entity_registry_enabled_by_default):
    _metadata_with_markers(hass)
    fake.reads["bc1/DHWTemp"] = "-40.0"                 # marked, equal: no sensor
    fake.reads["bc1/HydraulicSeparatorTemp"] = "-39.5"  # marked, near: a real (cold) value
    fake.reads["bc2/DHWTemp"] = "-40.0"                 # not marked: shown as read
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    assert entry.runtime_data.model.version == "0.5.9"
    absent = state_of(hass, entry, "bc1/DHWTemp/value")
    assert absent.state == STATE_UNKNOWN and absent.attributes["no_sensor"] is True
    near = state_of(hass, entry, "bc1/HydraulicSeparatorTemp/value")
    assert float(near.state) == -39.5 and "no_sensor" not in near.attributes
    unmarked = state_of(hass, entry, "bc2/DHWTemp/value")
    assert float(unmarked.state) == -40.0 and "no_sensor" not in unmarked.attributes
    # the sensor is fitted again (or the marker was wrong): the value shows, the attribute goes
    hub = entry.runtime_data
    hub.store("bc1/DHWTemp", ("48.5",))
    await hass.async_block_till_done()
    fitted = state_of(hass, entry, "bc1/DHWTemp/value")
    assert float(fitted.state) == 48.5 and "no_sensor" not in fitted.attributes


async def test_without_markers_nothing_changes(hass, fake, entity_registry_enabled_by_default):
    """The shipped definitions (0.5.8) carry no marker: −40.0 is shown as read, as before."""
    fake.reads["bc1/DHWTemp"] = "-40.0"
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    state = state_of(hass, entry, "bc1/DHWTemp/value")
    assert float(state.state) == -40.0 and "no_sensor" not in state.attributes
