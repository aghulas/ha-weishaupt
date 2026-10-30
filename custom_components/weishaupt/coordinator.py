"""Polling of the registers and guarded writes."""
from __future__ import annotations

import logging
from functools import partial

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_TELEGRAM_DB, CONF_WRITES_ENABLED, DEFAULT_TELEGRAM_DB, DOMAIN, SCAN_INTERVAL
from .guard import ServiceToolState, WriteGuard, WriteRefused, last_service_tool_telegram
from .protocol import EbusdClient, EbusdError
from .registers import DEVICES, Device, registers_of

_LOGGER = logging.getLogger(__name__)

type WeishauptConfigEntry = ConfigEntry[WeishauptCoordinator]


class WeishauptCoordinator(DataUpdateCoordinator[dict[str, dict[str, bytes | None]]]):
    """Data: device key -> register -> raw 2 bytes (None = register not used on that device)."""

    def __init__(self, hass: HomeAssistant, entry: WeishauptConfigEntry, client: EbusdClient) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.client = client
        self._db_path = entry.options.get(CONF_TELEGRAM_DB, DEFAULT_TELEGRAM_DB)
        self.guard = WriteGuard(entry.options.get(CONF_WRITES_ENABLED, False))

    async def _async_update_data(self) -> dict[str, dict[str, bytes | None]]:
        data = {}
        try:
            for device in DEVICES:
                data[device.key] = await self.client.read_registers(device.zz, registers_of(device))
        except (OSError, TimeoutError, EbusdError) as err:
            raise UpdateFailed(f"lecture ebusd : {err}") from err
        return data

    async def async_write(self, device: Device, register: str, raw: bytes, value: float,
                          minimum: float, maximum: float, source: str | None) -> None:
        """ÉCRITURE: guarded write of one register, read back; raises HomeAssistantError if refused or not taken."""
        register_id = f"{device.key}:{register}"
        service_tool = None
        if source == "ff":
            try:
                service_tool = ServiceToolState(await self.hass.async_add_executor_job(
                    partial(last_service_tool_telegram, self._db_path)))
            except Exception as err:  # noqa: BLE001 - any failure: the guard refuses the write
                service_tool = ServiceToolState(error=str(err))
        try:
            self.guard.check(register_id, value, minimum, maximum, source, service_tool)
        except WriteRefused as err:
            _LOGGER.warning("ÉCRITURE refusée %s = %s : %s", register_id, value, err)
            raise HomeAssistantError(f"Écriture refusée : {err}") from err
        self.guard.record(register_id, source)
        before = (self.data or {}).get(device.key, {}).get(register)
        try:
            await self.client.write_register(device.zz, register, raw, source)
            after = (await self.client.read_registers(device.zz, [register]))[register]
        except (OSError, TimeoutError, EbusdError) as err:
            _LOGGER.error("ÉCRITURE en échec %s = %s depuis %s : %s", register_id, value, source or "31", err)
            raise HomeAssistantError(f"Écriture en échec : {err}") from err
        _LOGGER.info("ÉCRITURE %s = %s (brut %s, avant %s, relu %s) depuis %s", register_id, value, raw.hex(),
                     before.hex() if before else None, after.hex() if after else None, source or "31")
        self.hass.bus.async_fire(f"{DOMAIN}_write", {
            "device": device.key, "register": register, "value": value, "source": source or "31",
            "before": before.hex() if before else None, "after": after.hex() if after else None})
        if self.data is not None:
            self.data[device.key][register] = after
            self.async_update_listeners()
        if after != raw:
            raise HomeAssistantError(f"Écriture non retenue par {device.name} (relu {after.hex() if after else None})")
