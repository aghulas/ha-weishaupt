"""Entities the metadata in use no longer yields: removed from the registry, unless the user customised them."""
from __future__ import annotations

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from custom_components.weishaupt import yielded
from custom_components.weishaupt.const import DOMAIN
from ha_common import make_entry, setup


async def test_stale_entities_removed_customised_ones_kept(hass, fake):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    registry = er.async_get(hass)
    plain = registry.async_get_or_create("sensor", DOMAIN, f"{entry.entry_id}_fs1/PowerDemand/ukn2",
                                         config_entry=entry).entity_id
    renamed = registry.async_get_or_create("sensor", DOMAIN, f"{entry.entry_id}_fs1/PowerDemand/ukn9",
                                           config_entry=entry).entity_id
    registry.async_update_entity(renamed, name="My own name")
    hidden = registry.async_get_or_create("sensor", DOMAIN, f"{entry.entry_id}_fs1/PowerDemand/ukn5",
                                          config_entry=entry).entity_id
    registry.async_update_entity(hidden, hidden_by=er.RegistryEntryHider.USER)
    # a setting whose number this version no longer yields as a sensor key of another platform: still yielded
    kept_value = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_bc1/SupplyTemp/value")
    # another integration's entity with the same unique id shape is never touched
    other = registry.async_get_or_create("sensor", "other", f"{entry.entry_id}_fs1/PowerDemand/ukn2").entity_id
    before = len(registry.entities)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert registry.async_get(plain) is None
    assert registry.async_get(renamed) is not None and registry.async_get(hidden) is not None
    assert registry.async_get(kept_value) is not None and registry.async_get(other) is not None
    assert len(registry.entities) == before - 1
    issue = ir.async_get(hass).async_get_issue(DOMAIN, f"stale_entities_{entry.entry_id}")
    assert issue is not None and renamed in issue.translation_placeholders["entities"]
    assert hidden in issue.translation_placeholders["entities"]
    # removed by the user: the issue goes at the next reload
    registry.async_remove(renamed)
    registry.async_remove(hidden)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"stale_entities_{entry.entry_id}") is None


async def test_every_created_entity_is_yielded(hass, fake, entity_registry_enabled_by_default):
    """Nothing the integration creates itself, with writes on, is taken for stale."""
    entry = make_entry(hass, fake, writes_enabled=True)
    await setup(hass, entry)
    keep = yielded(entry.runtime_data)
    prefix = f"{entry.entry_id}_"
    created = {(e.domain, e.unique_id.removeprefix(prefix))
               for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)}
    assert created and created <= keep
