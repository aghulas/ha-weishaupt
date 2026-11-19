"""Diagnostics download: what ebusd reported, what was compared, how the reader fares.

Nothing that identifies a site: the address of ebusd is redacted, and the bus gives no serial number. The values
read are included (temperatures, counters, settings): they are what a report about another boiler model or
software version needs."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .hub import WeishauptConfigEntry
from .model import ACCEPTED_DEFINITIONS

TO_REDACT = {CONF_HOST, "unique_id", "title", "telegram_db"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: WeishauptConfigEntry) -> dict[str, Any]:
    hub = entry.runtime_data
    info = hub.info
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
        "slaves_without_definitions": [a.address for a in hub.unknown_slaves],
        "reader": hub.snapshot() | asdict(hub.statistics),
        "writes": hub.writer.snapshot() if hub.writer is not None else {"enabled_in_options": False},
        "readings": {key: ";".join(reading.values) for key, reading in sorted(hub.readings.items())},
    }
