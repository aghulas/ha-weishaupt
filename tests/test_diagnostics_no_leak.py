"""The diagnostics download names no site and no person: not the address of ebusd, not the path of the telegram
log, not a Home Assistant user id, even inside error texts."""
from __future__ import annotations

import json

from custom_components.weishaupt.diagnostics import async_get_config_entry_diagnostics
from ha_common import make_entry, setup
from test_ha_programs import log  # noqa: F401  (a fixture)


async def test_no_host_path_or_user_id_leaks(hass, fake, log, hass_admin_user):
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    hub = entry.runtime_data
    writer = hub.writer
    writer.set_switch(True)
    await writer.async_write("em2/RoomNormalTemp", 22.0, hass_admin_user.id)
    # an error that names ebusd's address, as a lost connection does
    hub.statistics.last_error = f"cannot connect to ebusd: Connect call failed ('127.0.0.1', {fake.port})"
    # the entry id inside a text and a nested snapshot, as an issue id or a unique id would carry it
    hub.metadata_refused = {"note": f"definitions_file_{entry.entry_id}"}
    data = await async_get_config_entry_diagnostics(hass, entry)
    text = json.dumps(data)
    assert hass_admin_user.id not in text
    assert "127.0.0.1" not in text
    assert entry.entry_id not in text  # the entry id, as a key's value and inside texts
    assert data["entry"]["entry_id"] == "**REDACTED**"
    assert str(log) not in text
    assert data["writes"]["journal"][0]["user_id"] == "**REDACTED**"
    assert "user_id" in data["redacted"]
    # what a bug report needs is still there
    assert data["definitions"]["metadata_version"] and data["readings"] and data["ebusd"]["addresses"]
    assert "queue" in data["reader"] and data["scan_incomplete"] == []
