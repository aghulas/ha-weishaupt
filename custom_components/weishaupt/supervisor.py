"""The ebusd add-ons of Home Assistant OS, from the Supervisor's list of installed add-ons. Read only: the
integration never starts, stops, installs or configures an add-on (stopping one would cut ebusd for every other
client, MQTT included; which ebusd runs is the installation's decision)."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.helpers.hassio import is_hassio

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Addon:
    slug: str
    name: str
    state: str  # "started", "stopped", … as the Supervisor reports it
    port: int = 8888  # ebusd's TCP command port inside the add-on network

    @property
    def host(self) -> str:
        """Host name of the add-on on Home Assistant's internal network: the slug with "-" for "_"."""
        return self.slug.replace("_", "-")

    @property
    def started(self) -> bool:
        return self.state == "started"


def is_ebusd(slug: str) -> bool:
    """An ebusd add-on: `ebusd`, `<repository prefix>_ebusd`, or `<prefix>_ebusd_<variant>` (a test build)."""
    return "ebusd" in slug.lower().split("_")


def ebusd_addons(hass: HomeAssistant) -> list[Addon]:
    """The installed ebusd add-ons, by name; empty without the Supervisor or when its list is not ready."""
    if not is_hassio(hass):
        return []
    try:
        from homeassistant.components.hassio import get_addons_list
        addons = get_addons_list(hass) or []
    except Exception as err:  # noqa: BLE001 — the list is a convenience: without it, endpoints are typed by hand
        _LOGGER.debug("add-on list of the Supervisor not available: %s", err)
        return []
    found = [Addon(str(a.get("slug")), str(a.get("name") or a.get("slug")), str(a.get("state") or ""))
             for a in addons if a.get("slug") and is_ebusd(str(a["slug"]))]
    return sorted(found, key=lambda a: (a.name.lower(), a.slug))


def addon_states(hass: HomeAssistant) -> dict[str, str]:
    """State of each ebusd add-on by slug."""
    return {a.slug: a.state for a in ebusd_addons(hass)}
