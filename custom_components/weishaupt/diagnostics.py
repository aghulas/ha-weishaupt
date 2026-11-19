"""Diagnostics download: what ebusd reported, what was compared, how the reader fares.

Nothing that identifies a site or a person: the address of ebusd, the path of the telegram log, the title of the
entry, its id and the Home Assistant user ids of the write journal are redacted, and the bus gives no serial number. The
values read are included (temperatures, counters, settings): they are what a report about another boiler model or
software version needs. A test checks that none of the redacted values appears anywhere in this data.

Home Assistant wraps it in a download that also holds `setup_times` (keyed by the entry id) and the domain's open
repair issues (whose ids contain the entry id); an integration has no hook on those parts."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import REDACTED, async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .hub import WeishauptConfigEntry
from .const import DOMAIN
from .model import ACCEPTED_DEFINITIONS

# keys redacted wherever they appear (async_redact_data walks nested dicts and lists)
TO_REDACT = {CONF_HOST, "unique_id", "entry_id", "title", "telegram_db", "user_id", "context_user_id"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: WeishauptConfigEntry) -> dict[str, Any]:
    # the values behind the redacted keys also appear inside texts (an error naming ebusd's address, a path):
    # replaced wherever they are found
    secrets = [str(v) for v in (entry.data.get(CONF_HOST), entry.options.get("telegram_db"), entry.unique_id,
                                entry.entry_id) if v and len(str(v)) > 2]
    secrets += [user.id for user in await hass.auth.async_get_users()]
    data = async_redact_data(_collect(hass, entry), TO_REDACT)
    return _scrub(data, sorted(set(secrets), key=len, reverse=True)) | {"redacted": sorted(TO_REDACT)}


def _scrub(value: Any, secrets: list[str]) -> Any:
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, REDACTED)
        return value
    if isinstance(value, dict):
        return {_scrub(k, secrets): _scrub(v, secrets) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub(v, secrets) for v in value]
    return value


def _collect(hass: HomeAssistant, entry: WeishauptConfigEntry) -> dict[str, Any]:
    hub = entry.runtime_data
    info = hub.info
    watch = hass.data.get(f"{DOMAIN}_device_watch", {}).get(entry.entry_id)
    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "definitions": {
            "metadata_version": hub.model.version, "metadata_commit": hub.model.commit,
            "metadata_source": hub.metadata_source, "metadata_files_refused": hub.metadata_refused,
            "entities_named_from_metadata": sorted(hub.named_from_metadata),
            "entities_waiting_for_names": sorted(hub.not_named),
            "accepted": ACCEPTED_DEFINITIONS, "messages_in_metadata": len(hub.model.messages),
            "messages_usable": len(hub.usable),
            "mismatches": [asdict(m) for m in hub.mismatches],
        },
        "ebusd": {
            "version": info.version if info else None,
            "signal": info.signal if info else None,
            "addresses": [
                {"address": a.address, "role": a.role, "own": a.own, "manufacturer": a.manufacturer,
                 "ident": a.ident, "software": a.software, "hardware": a.hardware, "files": list(a.files)}
                for a in (info.addresses.values() if info else ())],
            "commands_sent": dict(hub.client.requests),
        },
        "devices": sorted(hub.devices),
        "scan_incomplete": hub.scan_incomplete,
        "devices_absent_since": watch.snapshot() if watch is not None else {},
        "slaves_without_definitions": [a.address for a in hub.unknown_slaves],
        "reader": hub.snapshot() | asdict(hub.statistics) | {"queue": hub.queue_state(),
                                                            "read_once_queued": len(hub._once)},
        "writes": hub.writer.snapshot() if hub.writer is not None else {"enabled_in_options": False},
        "readings": {key: ";".join(reading.values) for key, reading in sorted(hub.readings.items())},
    }
