"""Polling of the registers and guarded writes."""
from __future__ import annotations

import asyncio
import logging
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import CONF_TELEGRAM_DB, CONF_WRITES_ENABLED, DEFAULT_TELEGRAM_DB, DOMAIN, SCAN_INTERVAL
from .guard import ServiceToolState, WriteGuard, WriteRefused, read_service_tool_state
from .protocol import EbusdClient, EbusdError, datetime_broadcast_command
from .registers import DEVICES, Device, program_registers, registers_of

_LOGGER = logging.getLogger(__name__)
PROGRAM_INTERVAL = 3600.0  # time programs change rarely: read them once an hour

type WeishauptConfigEntry = ConfigEntry[WeishauptCoordinator]


class WeishauptCoordinator(DataUpdateCoordinator[dict[str, dict[str, bytes | None]]]):
    """Data: device key -> register -> raw 2 bytes (None = register not used on that device)."""

    def __init__(self, hass: HomeAssistant, entry: WeishauptConfigEntry, client: EbusdClient) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.client = client
        self._db_path = entry.options.get(CONF_TELEGRAM_DB, DEFAULT_TELEGRAM_DB)
        self.guard = WriteGuard(entry.options.get(CONF_WRITES_ENABLED, False))
        self._programs_read = 0.0

    async def _async_update_data(self) -> dict[str, dict[str, bytes | None]]:
        read_programs = time.monotonic() - self._programs_read > PROGRAM_INTERVAL or not self.data
        data = {}
        try:
            for device in DEVICES:
                values = dict((self.data or {}).get(device.key, {}))
                values.update(await self.client.read_registers(device.zz, registers_of(device)))
                if read_programs:
                    values.update(await self.client.read_registers(device.zz, program_registers()))
                data[device.key] = values
        except (OSError, TimeoutError, EbusdError) as err:
            raise UpdateFailed(f"lecture ebusd : {err}") from err
        if read_programs:
            self._programs_read = time.monotonic()
        return data

    async def async_write(self, device: Device, register: str, raw: bytes, value: float,
                          minimum: float, maximum: float, source: str | None) -> None:
        """ÉCRITURE: guarded write of one register, read back; raises HomeAssistantError if refused or not taken."""
        register_id = f"{device.key}:{register}"
        service_tool = None
        if source == "ff":
            try:
                service_tool = await self.hass.async_add_executor_job(read_service_tool_state, self._db_path)
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

    async def async_set_clock(self, align: bool = True) -> None:
        """ÉCRITURE (diffusion): set the regulators' clock from Home Assistant's time, by broadcasting `fe 0700`.

        Sets the clock master f1 (hour and minute); f1 restarts its seconds at 00 and redistributes the date to every
        module within about two minutes. `align` waits for the top of the next minute (sent at second 00) so the clock
        is right to about a second. The outside-temperature field is copied from f1's last broadcast."""
        try:
            self.guard.check_broadcast()
        except WriteRefused as err:
            _LOGGER.warning("ÉCRITURE horloge refusée : %s", err)
            raise HomeAssistantError(f"Écriture refusée : {err}") from err
        outside = await self.client.last_outside_raw() or b"\x00\x00"
        if align:
            now = dt_util.now()
            delay = (60 - now.second) - now.microsecond / 1e6
            if 0 < delay < 60:
                await asyncio.sleep(delay)
        when = dt_util.now()
        command = datetime_broadcast_command(0, when.minute, when.hour, when.day, when.month,
                                             when.isoweekday(), when.year % 100, outside)
        self.guard.record_broadcast()
        try:
            await self.client.broadcast_datetime(command)
        except (OSError, TimeoutError, EbusdError) as err:
            _LOGGER.error("ÉCRITURE horloge en échec : %s", err)
            raise HomeAssistantError(f"Écriture horloge en échec : {err}") from err
        _LOGGER.info("ÉCRITURE horloge diffusée %s (temp ext %s) : %s",
                     when.strftime("%Y-%m-%d %H:%M:%S"), outside.hex(), command)
        self.hass.bus.async_fire(f"{DOMAIN}_set_clock", {
            "when": when.isoformat(), "outside": outside.hex(), "command": command})
