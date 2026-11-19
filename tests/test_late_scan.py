"""ebusd restarted and still scanning the bus when the entry loads: the entry waits for the scan instead of
comparing with a partial view; the entities stay in the registry meanwhile; nothing is taken for stale."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

import custom_components.weishaupt as integration
from custom_components.weishaupt.const import DOMAIN
from ha_common import make_entry, setup, wait_until
from test_ha_programs import log  # noqa: F401  (a fixture)


def _scanning(fake, address: str, circuit: str) -> tuple[str, str]:
    """ebusd right after its restart: the address listed, not scanned, its definitions not loaded yet."""
    info, definitions = fake.info, fake.definitions[circuit]
    fake.info = "\n".join(f"address {address}: slave" if line.startswith(f"address {address}:") else line
                          for line in info.splitlines())
    fake.definitions[circuit] = ""
    return info, definitions


async def test_the_entry_waits_for_a_late_scan(hass, fake, log):
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    registry = er.async_get(hass)
    before = {e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)}
    writable = len(entry.runtime_data.writer.specs)
    info, definitions = _scanning(fake, "51", "em2")
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_em2/RoomNormalTemp/value") or \
        registry.async_get_entity_id("number", DOMAIN, f"{entry.entry_id}_em2/RoomNormalTemp/value")
    assert {e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)} == before
    assert hass.states.get(entity_id) is None or hass.states.get(entity_id).state == "unavailable"
    assert not [i for i in ir.async_get(hass).issues.values() if i.domain == DOMAIN
                and i.translation_key == "definitions_mismatch"]
    # the scan ends; Home Assistant's next try loads the entry as before
    fake.info, fake.definitions["em2"] = info, definitions
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=90))
    await wait_until(lambda: entry.state is ConfigEntryState.LOADED)
    await hass.async_block_till_done()
    hub = entry.runtime_data
    assert hub.scan_incomplete == [] and hub.mismatches == []
    assert len(hub.writer.specs) == writable
    assert {e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)} == before


async def test_after_the_wait_it_goes_on_without_removing_anything(hass, fake, log, monkeypatch):
    """Still not scanned after the wait: the entry loads with what ebusd has, names what is missing, and the
    stale-entity removal does not run on that partial view."""
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
    await setup(hass, entry)
    registry = er.async_get(hass)
    before = {e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)}
    _scanning(fake, "51", "em2")
    monkeypatch.setattr(integration, "SCAN_WAIT", 0)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.scan_incomplete == ["em2 (51): definitions not loaded yet"]
    assert {e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)} == before


async def test_a_device_seen_before_and_not_back_yet_is_waited_for(hass, fake, log):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    info = fake.info
    fake.remove_address("52")
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY
    fake.info = info
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=90))
    await wait_until(lambda: entry.state is ConfigEntryState.LOADED)
    await hass.async_block_till_done()


async def test_a_first_start_does_not_wait_for_devices_it_never_saw(hass, fake):
    fake.remove_address("52")
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    assert entry.state is ConfigEntryState.LOADED and "module3" not in entry.runtime_data.devices
