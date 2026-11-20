"""Weishaupt WTC boilers and WCM controllers through ebusd — unofficial.

Devices, entities and names come from the metadata file of a release of the Weishaupt definitions for ebusd
(`metadata.json`). At start-up what ebusd loaded is compared with it; a difference raises a repair issue and the
messages concerned get no entity. Reading is all it does unless writes are enabled in the options: then the
settings the definitions prove writable become number entities, written through the guard (`writer.py`).
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, device_registry as dr, entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .const import CONF_WRITES_ENABLED, DOCUMENTATION_URL, DOMAIN
from .devices import DeviceWatch
from .ebusd import EbusdClient, EbusdError
from .entity import device_identifier, hub_identifier
from .hub import Hub, WeishauptConfigEntry
from .metadata_file import FOLDER as METADATA_FOLDER, choose
from .model import ACCEPTED_DEFINITIONS, WEEKDAYS
from .panel import async_setup_panel
from .services import async_register_services
from .writer import Writer

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.NUMBER, Platform.SELECT, Platform.SENSOR,
             Platform.SWITCH, Platform.TEXT]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
EXAMPLES = 8  # messages named in the repair issue
SCAN_WAIT = 300  # seconds an entry waits for ebusd to finish its scan before going on with a partial view
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """The action of the integration (`services.py`) and the panel (`panel.py`), registered once whatever the
    entries."""
    async_register_services(hass)
    integration = await async_get_integration(hass, DOMAIN)
    await async_setup_panel(hass, str(integration.version))
    return True


async def async_setup_entry(hass: HomeAssistant, entry: WeishauptConfigEntry) -> bool:
    choice = await hass.async_add_executor_job(choose, Path(hass.config.path(METADATA_FOLDER)))
    hub = Hub(hass, entry, EbusdClient(entry.data[CONF_HOST], entry.data[CONF_PORT]), choice.model)
    hub.metadata_source, hub.metadata_refused = choice.source, choice.refused
    if choice.source != "bundled":
        hub.translated = await hass.async_add_executor_job(_bundled_names)

    registry = dr.async_get(hass)
    prefix = f"{entry.entry_id}_"
    expected = {identifier.removeprefix(prefix) for device in dr.async_entries_for_config_entry(registry, entry.entry_id)
                for domain, identifier in device.identifiers if domain == DOMAIN and identifier.startswith(prefix)}
    try:
        await hub.async_setup(expected)
    except EbusdError as err:
        raise ConfigEntryNotReady(translation_domain=DOMAIN, translation_key="cannot_connect",
                                  translation_placeholders={"error": str(err)}) from err
    waiting = hass.data.setdefault(f"{DOMAIN}_waiting_for_scan", {})
    if hub.scan_incomplete:
        # ebusd answers but is still scanning the bus (after its restart): wait for it rather than compare with a
        # partial view, which would raise a mismatch, offer fewer writes and could take entities for stale. Home
        # Assistant retries with a growing delay; the entities stay in the registry, unavailable, meanwhile.
        started = waiting.setdefault(entry.entry_id, time.monotonic())
        if time.monotonic() - started < SCAN_WAIT:
            _LOGGER.info("ebusd has not finished its scan (%s): waiting", "; ".join(hub.scan_incomplete))
            raise ConfigEntryNotReady(translation_domain=DOMAIN, translation_key="scan_incomplete",
                                      translation_placeholders={"missing": "; ".join(hub.scan_incomplete)})
        _LOGGER.warning("ebusd has still not scanned everything after %d s (%s): going on with what it has",
                        SCAN_WAIT, "; ".join(hub.scan_incomplete))
    waiting.pop(entry.entry_id, None)
    kept = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if kept is not None:  # a reload: what was read and listened to before
        hub.previously_listened = kept["listened"]
        hub.restore(kept["readings"])
    hub.urgent_at_start = hass.data.get(f"{DOMAIN}_enabled_by_migration", {}).pop(entry.entry_id, set())
    if entry.options.get(CONF_WRITES_ENABLED):
        hub.writer = Writer(hass, hub, dict(entry.options))
        try:
            await hub.writer.async_setup()
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
    _update_file_issue(hass, entry, hub)
    _remove_stale(hass, entry, hub)
    watch = DeviceWatch(hass, entry, hub)
    hass.data.setdefault(f"{DOMAIN}_device_watch", {})[entry.entry_id] = watch
    await watch.async_start()
    entry.async_create_background_task(hass, hub.async_run(), f"{DOMAIN} reader")
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


def yielded(hub: Hub) -> set[tuple[str, str]]:
    """(platform, key) of every entity the metadata in use can yield, whatever the options and the devices on the
    bus: what is not in it was created from an older metadata and is gone for good."""
    model = hub.model
    found = {(d.platform, d.key) for d in model.value_entities}
    found |= {("sensor", d.key) for d in model.group_entities}
    found |= {(d.platform, d.key) for d in model.setting_entities}
    found |= {("text", f"{group.key}/{day}") for group in model.writable_programs for day in WEEKDAYS}
    found |= {("sensor", "broadcast/Datetime/offset"), ("button", "broadcast/Datetime/set"), ("switch", "writes")}
    return found


# Options of a registry entry the user sets in the entity's settings dialog; Home Assistant itself writes others
# (a sensor's suggested display precision, the exposure to assistants), which are not a change by the user.
USER_OPTIONS = ("display_precision", "unit_of_measurement")
OLD_ENTITIES_SHOWN = 30  # entity ids named in the repair of the older-scheme entities


def current_scheme(suffix: str) -> bool:
    """Whether a unique id (without its entry id) follows the scheme of 0.2 and later: `<circuit>/<message>/<field>`,
    `<circuit>/group/<id>`, `<circuit>/<program>/<day>`, `broadcast/Datetime/…`, or `writes`. Version 0.1 built
    `<device>_<key>` (and `writes_enabled`): those are never removed without the user's confirmation."""
    return suffix == "writes" or "/" in suffix


def _customised(item: er.RegistryEntry) -> bool:
    """Whether the user changed an entity: a name, an icon, an area, labels, aliases, a category, hidden or disabled
    it, or set its display precision or unit. Such an entity is never removed."""
    aliases = [alias for alias in item.aliases if isinstance(alias, str)]  # not the default "its own name"
    user_options = any(key in options for options in item.options.values() if isinstance(options, dict)
                       for key in USER_OPTIONS)
    return bool(item.name or item.icon or item.area_id or item.labels or aliases or item.categories
                or item.hidden_by == er.RegistryEntryHider.USER or item.disabled_by == er.RegistryEntryDisabler.USER
                or user_options)


def older_entities(hass: HomeAssistant, entry: ConfigEntry) -> list[str]:
    """Entity ids of this entry left by version 0.1 (another unique-id scheme)."""
    prefix = f"{entry.entry_id}_"
    return sorted(item.entity_id for item in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
                  if item.platform == DOMAIN and item.unique_id.startswith(prefix)
                  and not current_scheme(item.unique_id.removeprefix(prefix)))


def _remove_stale(hass: HomeAssistant, entry: ConfigEntry, hub: Hub) -> None:
    """Entities of this entry, in the current unique-id scheme, that the metadata in use no longer yields (a
    definitions release marked a field skip, or dropped a message): removed from the registry, as integrations do
    with stale entities, unless the user customised them; those stay, and one repair issue names them.

    Entities of another scheme (left by version 0.1) are never removed here: one repair lists them and removes them
    only when the user confirms it."""
    if hub.scan_incomplete or any(m.reason == "missing" for m in hub.mismatches):
        # a partial view of the bus (ebusd still scanning, definitions not loaded): nothing is removed from it
        _LOGGER.info("stale entities not looked for: ebusd's view of the bus is not complete")
        update_older_issue(hass, entry)
        return
    registry = er.async_get(hass)
    keep = yielded(hub)
    prefix = f"{entry.entry_id}_"
    kept = []
    for item in er.async_entries_for_config_entry(registry, entry.entry_id):
        if item.platform != DOMAIN or not item.unique_id.startswith(prefix):
            continue
        suffix = item.unique_id.removeprefix(prefix)
        if not current_scheme(suffix) or (item.domain, suffix) in keep:
            continue
        if _customised(item):
            kept.append(item.entity_id)
            continue
        _LOGGER.info("%s removed: the definitions %s no longer have it", item.entity_id, hub.model.version)
        registry.async_remove(item.entity_id)
    issue = f"stale_entities_{entry.entry_id}"
    if kept:
        ir.async_create_issue(
            hass, DOMAIN, issue, is_fixable=False, severity=ir.IssueSeverity.WARNING,
            translation_key="stale_entities", learn_more_url=DOCUMENTATION_URL,
            translation_placeholders={"version": hub.model.version, "entities": ", ".join(sorted(kept))})
    else:
        ir.async_delete_issue(hass, DOMAIN, issue)
    update_older_issue(hass, entry)


def update_older_issue(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """One fixable repair while entities of version 0.1 remain: its dialog lists them and removes them on the
    user's confirmation."""
    issue = f"old_entities_{entry.entry_id}"
    older = older_entities(hass, entry)
    if not older:
        ir.async_delete_issue(hass, DOMAIN, issue)
        return
    shown = ", ".join(older[:OLD_ENTITIES_SHOWN]) + (" …" if len(older) > OLD_ENTITIES_SHOWN else "")
    ir.async_create_issue(
        hass, DOMAIN, issue, is_fixable=True, severity=ir.IssueSeverity.WARNING, translation_key="old_entities",
        learn_more_url=DOCUMENTATION_URL, data={"entry_id": entry.entry_id, "kind": "old_entities"},
        translation_placeholders={"count": str(len(older)), "entities": shown})


def _follow_renames(hass: HomeAssistant, entry: ConfigEntry, hub: Hub) -> None:
    """A definitions release renamed a message or a field: its entity keeps its registry entry (entity id, history,
    settings of the user) and gets the unique id built from the new name. Sensors and settings alike."""
    registry = er.async_get(hass)
    for description in [*hub.model.value_entities, *hub.model.setting_entities]:
        if description.former_key is None:
            continue
        old, new = (f"{entry.entry_id}_{key}" for key in (description.former_key, description.key))
        entity_id = registry.async_get_entity_id(description.platform, DOMAIN, old)
        if entity_id is not None and registry.async_get_entity_id(description.platform, DOMAIN, new) is None:
            registry.async_update_entity(entity_id, new_unique_id=new)


def _bundled_names() -> set[tuple[str, str]]:
    """(platform, translation key) and ("device", id) the translations shipped with the integration name."""
    names = json.loads((Path(__file__).parent / "translations" / "en.json").read_text(encoding="utf-8"))
    found = {(platform, key) for platform, items in names.get("entity", {}).items() for key in items}
    return found | {("device", key) for key in names.get("device", {})}


def _update_file_issue(hass: HomeAssistant, entry: ConfigEntry, hub: Hub) -> None:
    """A repair issue only when a metadata file beside the configuration was refused: a correct installation has
    none. Which definitions are in use, the entities named from the metadata and those waiting for a name go to an
    info line of the log and to the diagnostics."""
    _LOGGER.info("definitions in use: %s (%s); %d entities named from the metadata, %d waiting for a name%s",
                 hub.model.version, hub.metadata_source, len(hub.named_from_metadata), len(hub.not_named),
                 f" ({', '.join(sorted(hub.not_named))})" if hub.not_named else "")
    issue = f"definitions_file_{entry.entry_id}"
    if not hub.metadata_refused:
        ir.async_delete_issue(hass, DOMAIN, issue)
        return
    ir.async_create_issue(
        hass, DOMAIN, issue, is_fixable=False, severity=ir.IssueSeverity.WARNING, translation_key="definitions_file",
        learn_more_url=DOCUMENTATION_URL, translation_placeholders={
            "source": hub.metadata_source, "version": hub.model.version,
            "refused": "; ".join(f"{name}: {why}" for name, why in sorted(hub.metadata_refused.items()))})


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
    # what was read before the reload: a message missing from it after the reload is read first
    hub = entry.runtime_data
    hub.async_close()  # the panel looks for the hub of the reloaded entry
    hass.data.get(f"{DOMAIN}_device_watch", {}).pop(entry.entry_id, None)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"listened": hub.listened(), "readings": dict(hub.readings)}
    if entry.runtime_data.writer is not None:
        entry.runtime_data.writer.drop_all_pending()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    from homeassistant.helpers.storage import Store
    await Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.writes").async_remove()
    await Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.devices").async_remove()
    for issue in ("no_devices", "definitions_mismatch", "definitions_file", "stale_entities", "old_entities"):
        ir.async_delete_issue(hass, DOMAIN, f"{issue}_{entry.entry_id}")


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Version 1 (0.1.x) kept the options of the write path of 0.1. They are dropped: writes are enabled again only
    by a decision in the options of this version.

    Version 2.1 (0.3.0b2) created the numbers of the regulation settings disabled; since 0.3.0rc1 every number is
    created enabled. 2.1 -> 2.2 enables, once, the numbers the integration itself disabled — never one a user
    disabled — and has them read first."""
    if entry.version == 1:
        hass.config_entries.async_update_entry(entry, options={}, version=2, minor_version=2)
    if entry.version == 2 and entry.minor_version < 2:
        registry = er.async_get(hass)
        enabled = set()
        for item in er.async_entries_for_config_entry(registry, entry.entry_id):
            if item.domain == "number" and item.disabled_by is er.RegistryEntryDisabler.INTEGRATION:
                registry.async_update_entity(item.entity_id, disabled_by=None)
                # unique id <entry id>_<circuit>/<name>/<field>: the message is <circuit>/<name>
                enabled.add("/".join(item.unique_id.removeprefix(f"{entry.entry_id}_").split("/")[:2]))
        hass.data.setdefault(f"{DOMAIN}_enabled_by_migration", {})[entry.entry_id] = enabled
        hass.config_entries.async_update_entry(entry, minor_version=2)
    return entry.version <= 2


async def async_remove_config_entry_device(hass: HomeAssistant, entry: WeishauptConfigEntry,
                                           device: dr.DeviceEntry) -> bool:
    """A device may be deleted by hand when it is no longer on the bus (or was created by version 0.1)."""
    hub = entry.runtime_data
    current = {hub_identifier(hub)} | {device_identifier(hub, d) for d in hub.devices.values()}
    return not current.intersection(device.identifiers)


async def _async_reload(hass: HomeAssistant, entry: WeishauptConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
