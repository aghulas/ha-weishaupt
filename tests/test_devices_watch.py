"""Devices that appear on the bus later (the entry reloads itself, nothing removed) and devices that left it (a
repair after 7 days; only the user's confirmation removes them)."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from custom_components.weishaupt import devices
from custom_components.weishaupt.const import DOMAIN
from ha_common import make_entry, setup, wait_until


def _watch(hass, entry):
    return hass.data[f"{DOMAIN}_device_watch"][entry.entry_id]


async def test_a_device_that_appears_later_reloads_the_entry(hass, fake):
    info = fake.info
    fake.remove_address("52")
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    assert "module3" not in entry.runtime_data.devices
    registry = er.async_get(hass)
    before = {e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)}
    fake.info = info  # module 3 answers now
    await _watch(hass, entry).async_check()
    await wait_until(lambda: entry.state is ConfigEntryState.LOADED and "module3" in entry.runtime_data.devices)
    await hass.async_block_till_done()
    after = {e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)}
    assert before < after  # only added


async def test_an_absent_device_gets_a_repair_after_seven_days_and_goes_only_when_confirmed(hass, fake):
    from homeassistant.components.repairs import repairs_flow_manager
    from homeassistant.setup import async_setup_component
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    watch = _watch(hass, entry)
    clock = [1_800_000_000.0]
    watch._now = lambda: clock[0]
    fake.remove_address("52")
    await watch.async_check()
    assert "module3" in watch.absent
    issues = ir.async_get(hass)
    assert issues.async_get_issue(DOMAIN, devices.issue_id(entry, "module3")) is None
    clock[0] += 6 * 86400
    await watch.async_check()
    assert issues.async_get_issue(DOMAIN, devices.issue_id(entry, "module3")) is None
    clock[0] += 1.1 * 86400
    await watch.async_check()
    issue = issues.async_get_issue(DOMAIN, devices.issue_id(entry, "module3"))
    assert issue is not None and issue.is_fixable and issue.translation_placeholders["days"] == "7"
    device = devices.registered(hass, entry)["module3"]
    assert dr.async_get(hass).async_get(device.id) is not None  # nothing removed without the user
    assert await async_setup_component(hass, "repairs", {})
    manager = repairs_flow_manager(hass)
    result = await manager.async_init(DOMAIN, data={"issue_id": issue.issue_id})
    assert result["type"] == "form"
    result = await manager.async_configure(result["flow_id"], {})
    assert result["type"] == "create_entry" and result["description"] == "removed"
    assert dr.async_get(hass).async_get(device.id) is None
    assert issues.async_get_issue(DOMAIN, devices.issue_id(entry, "module3")) is None


async def test_a_device_that_comes_back_clears_its_repair(hass, fake, hass_storage):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    watch = _watch(hass, entry)
    clock = [1_800_000_000.0]
    watch._now = lambda: clock[0]
    info = fake.info
    fake.remove_address("52")
    await watch.async_check()
    clock[0] += 8 * 86400
    await watch.async_check()
    assert ir.async_get(hass).async_get_issue(DOMAIN, devices.issue_id(entry, "module3")) is not None
    # kept across a restart
    assert "module3" in hass_storage[f"{DOMAIN}.{entry.entry_id}.devices"]["data"]["absent"]
    fake.info = info
    await watch.async_check()
    assert watch.absent == {}
    assert ir.async_get(hass).async_get_issue(DOMAIN, devices.issue_id(entry, "module3")) is None


async def test_ebusd_not_answering_concludes_nothing(hass, fake, monkeypatch):
    from custom_components.weishaupt.ebusd import EbusdConnectionError
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    watch = _watch(hass, entry)

    async def unreachable():
        raise EbusdConnectionError("cannot connect to ebusd")

    monkeypatch.setattr(entry.runtime_data.client, "info", unreachable)
    await watch.async_check()
    assert watch.absent == {}
