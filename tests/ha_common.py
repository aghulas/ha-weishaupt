"""Helpers of the tests that run inside a Home Assistant test instance."""
from __future__ import annotations

import asyncio

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.weishaupt.const import CONF_CYCLIC_INTERVAL, CONF_REQUEST_GAP, DOMAIN


def make_entry(hass: HomeAssistant, fake, gap: float = 0.0, **options) -> MockConfigEntry:
    """A config entry for the simulated ebusd. The gap between requests is 0 unless a test is about pacing."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=2, title="Weishaupt", unique_id=f"127.0.0.1:{fake.port}",
        data={CONF_HOST: "127.0.0.1", CONF_PORT: fake.port},
        options={CONF_REQUEST_GAP: gap, CONF_CYCLIC_INTERVAL: 300} | options)
    entry.add_to_hass(hass)
    return entry


async def setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def wait_until(condition, timeout: float = 20.0) -> None:
    """The reader is a background task on real time: wait for what it is expected to reach."""
    for _ in range(int(timeout / 0.02)):
        if condition():
            return
        await asyncio.sleep(0.02)
    raise AssertionError("condition not reached")


async def settled(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Wait until every message that is listened to has been asked once."""
    hub = entry.runtime_data
    await wait_until(lambda: hub.snapshot()["due_now"] == 0)
    await hass.async_block_till_done()


def state_of(hass: HomeAssistant, entry: MockConfigEntry, key: str, platform: str = "sensor"):
    """State of the entity of a metadata key (`bc1/SupplyTemp/value`): looked up by unique id, not by name."""
    entity_id = er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"{entry.entry_id}_{key}")
    assert entity_id is not None, key
    return hass.states.get(entity_id)
