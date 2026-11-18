"""Weishaupt WTC boilers and WCM controllers through ebusd — unofficial, read-only.

Devices, entities and names come from the metadata file of a release of the Weishaupt definitions for ebusd
(`metadata.json`). At start-up what ebusd loaded is compared with it; a difference raises a repair issue and the
messages concerned get no entity.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr, entity_registry as er, issue_registry as ir

from .const import DOCUMENTATION_URL, DOMAIN
from .ebusd import EbusdClient, EbusdError
from .entity import device_identifier, hub_identifier
from .hub import Hub, WeishauptConfigEntry
from .model import ACCEPTED_DEFINITIONS, Model

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]
EXAMPLES = 8  # messages named in the repair issue


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry) -> bool:
    model = await hass.async_add_executor_job(Model.load)
    hub = Hub(hass, entry, EbusdClient(entry.data[CONF_HOST], entry.data[CONF_PORT]), model)
    try:
        await hub.async_setup()
    except EbusdError as err:
        raise ConfigEntryNotReady(translation_domain=DOMAIN, translation_key="cannot_connect",
                                  translation_placeholders={"error": str(err)}) from err
    entry.runtime_data = hub
    assert hub.info is not None
    hub.device_id = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={hub_identifier(hub)}, name="ebusd", manufacturer="ebusd",
        sw_version=hub.info.version, entry_type=dr.DeviceEntryType.SERVICE).id
    _update_issues(hass, entry, hub)
    _follow_renames(hass, entry, hub)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_create_background_task(hass, hub.async_run(), f"{DOMAIN} reader")
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


def _follow_renames(hass: HomeAssistant, entry: ConfigEntry, hub: Hub) -> None:
    """A definitions release renamed a message: its entity keeps its registry entry (entity id, history,
    settings of the user) and gets the unique id built from the new name."""
    registry = er.async_get(hass)
    for description in hub.model.value_entities:
        if description.former_key is None:
            continue
        old, new = (f"{entry.entry_id}_{key}" for key in (description.former_key, description.key))
        entity_id = registry.async_get_entity_id(description.platform, DOMAIN, old)
        if entity_id is not None and registry.async_get_entity_id(description.platform, DOMAIN, new) is None:
            registry.async_update_entity(entity_id, new_unique_id=new)


def _update_issues(hass: HomeAssistant, entry: ConfigEntry, hub: Hub) -> None:
    """One repair issue when no known device answers, one when ebusd's definitions are not those expected."""
    no_devices, mismatch = f"no_devices_{entry.entry_id}", f"definitions_mismatch_{entry.entry_id}"
    if hub.devices:
        ir.async_delete_issue(hass, DOMAIN, no_devices)
    else:
        ir.async_create_issue(
            hass, DOMAIN, no_devices, is_fixable=False, severity=ir.IssueSeverity.WARNING,
            translation_key="no_devices", learn_more_url=DOCUMENTATION_URL,
            translation_placeholders={"addresses": ", ".join(a.address for a in hub.unknown_slaves) or "-"})
    if not hub.mismatches:
        ir.async_delete_issue(hass, DOMAIN, mismatch)
        return
    missing = sum(1 for m in hub.mismatches if m.reason == "missing")
    names = [m.key for m in hub.mismatches[:EXAMPLES]]
    if len(hub.mismatches) > EXAMPLES:
        names.append("…")
    ir.async_create_issue(
        hass, DOMAIN, mismatch, is_fixable=False, learn_more_url=DOCUMENTATION_URL,
        severity=ir.IssueSeverity.ERROR if not hub.usable else ir.IssueSeverity.WARNING,
        translation_key="definitions_mismatch",
        translation_placeholders={
            "count": str(len(hub.mismatches)), "missing": str(missing),
            "different": str(len(hub.mismatches) - missing), "version": hub.model.version,
            "accepted": ACCEPTED_DEFINITIONS, "messages": ", ".join(names)})


async def async_unload_entry(hass: HomeAssistant, entry: WeishauptConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    for issue in ("no_devices", "definitions_mismatch"):
        ir.async_delete_issue(hass, DOMAIN, f"{issue}_{entry.entry_id}")


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Version 1 (0.1.x) kept the options of the write path: they have no meaning in a read-only version."""
    if entry.version == 1:
        hass.config_entries.async_update_entry(entry, options={}, version=2)
    return entry.version <= 2


async def async_remove_config_entry_device(hass: HomeAssistant, entry: WeishauptConfigEntry,
                                           device: dr.DeviceEntry) -> bool:
    """A device may be deleted by hand when it is no longer on the bus (or was created by version 0.1)."""
    hub = entry.runtime_data
    current = {hub_identifier(hub)} | {device_identifier(hub, d) for d in hub.devices.values()}
    return not current.intersection(device.identifiers)


async def _async_reload(hass: HomeAssistant, entry: WeishauptConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
