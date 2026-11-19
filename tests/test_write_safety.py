"""Safety across restarts and reloads: the write switch comes back off; the guard's counters are kept."""
from __future__ import annotations

import time

import pytest
from homeassistant.core import State
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import mock_restore_cache

from custom_components.weishaupt.const import DOMAIN
from custom_components.weishaupt.guard import WriteRefused
from ha_common import make_entry, setup
from test_ha_programs import log  # noqa: F401  (a fixture)


def _switch(hass, entry):
    return er.async_get(hass).async_get_entity_id("switch", DOMAIN, f"{entry.entry_id}_writes")


async def test_switch_off_after_a_reload(hass, fake, log):
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    await hass.services.async_call("switch", "turn_on", {"entity_id": _switch(hass, entry)}, blocking=True)
    assert hass.states.get(_switch(hass, entry)).state == "on"
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(_switch(hass, entry)).state == "off" and not entry.runtime_data.writer.switch_on


async def test_switch_off_after_a_restart_whatever_it_was(hass, fake, log):
    """A state `on` restored by Home Assistant at its start is not taken over."""
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    registry = er.async_get(hass)
    entity_id = registry.async_get_or_create("switch", DOMAIN, f"{entry.entry_id}_writes",
                                             config_entry=entry).entity_id
    mock_restore_cache(hass, [State(entity_id, "on")])
    await setup(hass, entry)
    assert hass.states.get(entity_id).state == "off" and not entry.runtime_data.writer.switch_on


async def test_the_hourly_count_survives_a_reload(hass, fake, log):
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log, max_writes_per_hour=1)
    await setup(hass, entry)
    writer = entry.runtime_data.writer
    writer.set_switch(True)
    await writer.async_write("em2/RoomSetbackTemp", 21.0, None)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    writer = entry.runtime_data.writer
    assert writer.guard.writes_last_hour() == 1
    writer.set_switch(True)
    with pytest.raises(WriteRefused) as err:
        await writer.async_write("em2/RoomNormalTemp", 22.0, None)
    assert err.value.code == "hourly_limit" and len(fake.writes) == 1


async def test_the_counters_are_read_back_at_a_start(hass, fake, log, hass_storage):
    """What a start finds in the store: the writes of the last hour count, older ones and future ones do not;
    the 10 s per register holds too."""
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    register = entry.runtime_data.writer.specs["em2/RoomNormalTemp"].register_id
    now = time.time()
    hass_storage[f"{DOMAIN}.{entry.entry_id}.writes"] = {
        "version": 1, "minor_version": 1, "key": f"{DOMAIN}.{entry.entry_id}.writes",
        "data": {"writes": [now - 4000, now - 600, now - 2, now + 900],
                 "last_by_register": {register: now - 2, "08:0000": now - 4000}, "own_ff": [now - 2]}}
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    writer = entry.runtime_data.writer
    assert writer.guard.writes_last_hour() == 2
    writer.set_switch(True)
    with pytest.raises(WriteRefused) as err:
        await writer.async_write("em2/RoomNormalTemp", 22.0, None)
    assert err.value.code == "register_interval" and fake.writes == []


async def test_the_store_is_saved_before_the_write_is_sent(hass, fake, log, hass_storage):
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    writer = entry.runtime_data.writer
    writer.set_switch(True)
    await writer.async_write("em2/RoomNormalTemp", 22.0, None)
    await hass.async_block_till_done()
    saved = hass_storage[f"{DOMAIN}.{entry.entry_id}.writes"]["data"]
    assert len(saved["writes"]) == 1 and len(saved["last_by_register"]) == 1


async def test_the_switch_shows_each_write_at_once(hass, fake, log):
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    writer = entry.runtime_data.writer
    await hass.services.async_call("switch", "turn_on", {"entity_id": _switch(hass, entry)}, blocking=True)
    assert hass.states.get(_switch(hass, entry)).attributes["writes_last_hour"] == 0
    assert hass.states.get(_switch(hass, entry)).attributes["max_writes_per_hour"] == 30
    await writer.async_write("em2/RoomNormalTemp", 22.0, None)
    await hass.async_block_till_done()
    assert hass.states.get(_switch(hass, entry)).attributes["writes_last_hour"] == 1
