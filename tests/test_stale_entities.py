"""Entities the metadata in use no longer yields: removed from the registry only in the current unique-id scheme,
and unless the user customised them. Entities of version 0.1 (another scheme) only on the user's confirmation."""
from __future__ import annotations

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from custom_components.weishaupt import current_scheme, yielded
from custom_components.weishaupt.const import DOMAIN
from ha_common import make_entry, setup


def _add(registry, entry, platform: str, suffix: str) -> str:
    return registry.async_get_or_create(platform, DOMAIN, f"{entry.entry_id}_{suffix}", config_entry=entry).entity_id


async def _reload(hass, entry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()


async def test_stale_entities_removed_customised_ones_kept(hass, fake):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    registry = er.async_get(hass)
    plain = _add(registry, entry, "sensor", "fs1/PowerDemand/ukn2")
    renamed = _add(registry, entry, "sensor", "fs1/PowerDemand/ukn9")
    registry.async_update_entity(renamed, name="My own name")
    hidden = _add(registry, entry, "sensor", "fs1/PowerDemand/ukn5")
    registry.async_update_entity(hidden, hidden_by=er.RegistryEntryHider.USER)
    precision = _add(registry, entry, "sensor", "fs2/PowerDemand/ukn2")
    registry.async_update_entity_options(precision, "sensor", {"display_precision": 2})
    kept_value = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_bc1/SupplyTemp/value")
    other = registry.async_get_or_create("sensor", "other", f"{entry.entry_id}_fs1/PowerDemand/ukn2").entity_id
    before = len(registry.entities)
    await _reload(hass, entry)
    assert registry.async_get(plain) is None
    for entity_id in (renamed, hidden, precision, kept_value, other):
        assert registry.async_get(entity_id) is not None, entity_id
    assert len(registry.entities) == before - 1
    issue = ir.async_get(hass).async_get_issue(DOMAIN, f"stale_entities_{entry.entry_id}")
    assert issue is not None and not issue.is_fixable
    assert all(e in issue.translation_placeholders["entities"] for e in (renamed, hidden, precision))
    for entity_id in (renamed, hidden, precision):
        registry.async_remove(entity_id)
    await _reload(hass, entry)
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"stale_entities_{entry.entry_id}") is None


async def test_options_home_assistant_writes_are_no_customisation(hass, fake):
    """The false positive of 0.5.0b2: a sensor's suggested display precision and its exposure to assistants are
    written by Home Assistant, not by the user; such a stale entity is removed, without a repair."""
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    registry = er.async_get(hass)
    stale = _add(registry, entry, "sensor", "fs1/PowerDemand/dhwsettemp")
    registry.async_update_entity_options(stale, "sensor", {"suggested_display_precision": 1})
    registry.async_update_entity_options(stale, "conversation", {"should_expose": False})
    registry.async_update_entity_options(stale, "sensor.private", {"suggested_unit_of_measurement": "°C"})
    await _reload(hass, entry)
    assert registry.async_get(stale) is None
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"stale_entities_{entry.entry_id}") is None


async def test_entities_of_version_0_1_only_on_confirmation(hass, fake):
    """A registry that still holds what 0.1.3 created (`<entry>_<device>_<key>`, `writes_enabled`): nothing is
    removed at a load; one fixable repair lists them; its dialog removes them when confirmed, and only them."""
    from homeassistant.components.repairs import repairs_flow_manager
    from homeassistant.setup import async_setup_component
    entry = make_entry(hass, fake)
    registry = er.async_get(hass)
    old = [
        _add(registry, entry, "number", "fs1_consigne_eau_chaude"),
        _add(registry, entry, "date", "fs1_conges_debut"),
        _add(registry, entry, "switch", "writes_enabled"),
        _add(registry, entry, "sensor", "ka_cascade_temps_de_blocage"),
    ]
    registry.async_update_entity(old[0], name="Kept name")  # customised or not: an older scheme waits for the user
    await setup(hass, entry)
    for entity_id in old:
        assert registry.async_get(entity_id) is not None
    issue = ir.async_get(hass).async_get_issue(DOMAIN, f"old_entities_{entry.entry_id}")
    assert issue is not None and issue.is_fixable and issue.translation_placeholders["count"] == "4"
    await _reload(hass, entry)
    assert all(registry.async_get(entity_id) is not None for entity_id in old)  # still nothing at a reload
    current = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_bc1/SupplyTemp/value")
    assert await async_setup_component(hass, "repairs", {})
    manager = repairs_flow_manager(hass)
    result = await manager.async_init(DOMAIN, data={"issue_id": issue.issue_id})
    assert result["type"] == "form" and result["description_placeholders"]["count"] == "4"
    assert old[1] in result["description_placeholders"]["entities"]
    result = await manager.async_configure(result["flow_id"], {})
    assert result["type"] == "create_entry" and result["description"] == "removed"
    assert all(registry.async_get(entity_id) is None for entity_id in old)
    assert registry.async_get(current) is not None
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"old_entities_{entry.entry_id}") is None


def test_unique_id_schemes():
    assert current_scheme("bc1/SupplyTemp/value") and current_scheme("fs1/heating1/monday")
    assert current_scheme("bc1/group/faulthistory") and current_scheme("writes")
    assert not current_scheme("fs1_consigne_eau_chaude") and not current_scheme("writes_enabled")


async def test_every_created_entity_is_yielded(hass, fake, entity_registry_enabled_by_default):
    """Nothing the integration creates itself, with writes on, is taken for stale."""
    entry = make_entry(hass, fake, writes_enabled=True)
    await setup(hass, entry)
    keep = yielded(entry.runtime_data)
    prefix = f"{entry.entry_id}_"
    created = {(e.domain, e.unique_id.removeprefix(prefix))
               for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)}
    assert created and created <= keep
    assert all(current_scheme(key) for _, key in created)
