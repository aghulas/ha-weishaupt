"""Devices that appear on the bus after the entry was set up, and devices that left it.

Every `INTERVAL` the integration asks ebusd `info` (nothing goes to the bus):
- a device the metadata knows, now answering and not set up yet (added to the installation, or back after a long
  absence): the entry is reloaded once, which adds its entities; nothing is removed;
- a device of this entry no longer on the bus: the time it was first missed is kept (across restarts, in
  `.storage`); after `ABSENT_DAYS` a repair offers to remove it, and only the user's confirmation removes it (its
  entities go with it). A device that comes back clears its record and its repair."""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store

from .const import DOCUMENTATION_URL, DOMAIN
from .ebusd import EbusdError, EbusdInfo
from .hub import Hub

_LOGGER = logging.getLogger(__name__)
INTERVAL = timedelta(minutes=10)
ABSENT_DAYS = 7


def registered(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, dr.DeviceEntry]:
    """Device id of the metadata -> device registry entry, for the bus devices of this entry."""
    prefix = f"{entry.entry_id}_"
    found = {}
    for device in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id):
        for domain, identifier in device.identifiers:
            if domain == DOMAIN and identifier.startswith(prefix):
                found[identifier.removeprefix(prefix)] = device
    return found


def issue_id(entry: ConfigEntry, device_id: str) -> str:
    return f"device_absent_{entry.entry_id}_{device_id}"


class DeviceWatch:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, hub: Hub,
                 now: Callable[[], float] = time.time) -> None:
        self.hass, self.entry, self.hub, self._now = hass, entry, hub, now
        self._store: Store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.devices")
        self.absent: dict[str, float] = {}  # device id -> time it was first missed
        self._reloading = False

    async def async_start(self) -> None:
        self.absent = {k: v for k, v in ((await self._store.async_load()) or {}).get("absent", {}).items()
                       if isinstance(v, (int, float))}
        await self.async_check(self.hub.info)
        self.entry.async_on_unload(async_track_time_interval(self.hass, self._async_tick, INTERVAL))

    async def _async_tick(self, _now: Any) -> None:
        await self.async_check()

    async def async_check(self, info: EbusdInfo | None = None) -> None:
        if info is None:
            try:
                info = await self.hub.client.info()
            except EbusdError:
                return  # ebusd cannot be asked now: nothing is concluded
        slaves = {a.address for a in info.addresses.values() if a.role == "slave" and not a.own}
        present = self.hub.model.present_devices(slaves)
        new = sorted(set(present) - set(self.hub.devices))
        if new and not self._reloading:
            self._reloading = True
            _LOGGER.info("device(s) %s now on the bus: reloading the entry to add them", ", ".join(new))
            self.hass.config_entries.async_schedule_reload(self.entry.entry_id)
        now = self._now()
        known = registered(self.hass, self.entry)
        changed = False
        for device_id in known:
            if device_id not in self.hub.model.devices:
                continue  # the hub device, or a device of another metadata: not the bus's
            if device_id in present:
                if self.absent.pop(device_id, None) is not None:
                    changed = True
                    _LOGGER.info("device %s is back on the bus", device_id)
                ir.async_delete_issue(self.hass, DOMAIN, issue_id(self.entry, device_id))
                continue
            if device_id not in self.absent:
                self.absent[device_id] = now
                changed = True
                _LOGGER.info("device %s is not on the bus", device_id)
            days = (now - self.absent[device_id]) / 86400
            if days >= ABSENT_DAYS:
                label = self.hub.model.devices[device_id].label
                ir.async_create_issue(
                    self.hass, DOMAIN, issue_id(self.entry, device_id), is_fixable=True,
                    severity=ir.IssueSeverity.WARNING, translation_key="device_absent",
                    learn_more_url=DOCUMENTATION_URL,
                    translation_placeholders={"device": label.get(self.hass.config.language.split("-")[0],
                                                                  label["en"]),
                                              "days": str(int(days))},
                    data={"entry_id": self.entry.entry_id, "kind": "device_absent", "device": device_id})
        for device_id in [d for d in self.absent if d not in known]:  # removed meanwhile
            del self.absent[device_id]
            changed = True
        if changed:
            await self._store.async_save({"absent": self.absent})

    def snapshot(self) -> dict[str, float]:
        return {device_id: round((self._now() - since) / 86400, 2) for device_id, since in self.absent.items()}
