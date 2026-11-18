"""Configuration: where ebusd listens, with a connection test; options: the load put on the bus, and writes
(off unless enabled here; the write switch then turns them on and off)."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CYCLIC_INTERVAL,
    CONF_REQUEST_GAP,
    CONF_TELEGRAM_DB,
    CONF_WRITES_ENABLED,
    DEFAULT_CYCLIC_INTERVAL,
    DEFAULT_REQUEST_GAP,
    DEFAULT_TELEGRAM_DB,
    DOMAIN,
    MAX_CYCLIC_INTERVAL,
    MAX_REQUEST_GAP,
    MIN_CYCLIC_INTERVAL,
    MIN_REQUEST_GAP,
)
from .ebusd import DEFAULT_PORT, EbusdClient, EbusdError


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema({
        vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, vol.UNDEFINED)): str,
        vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)),
    })


async def _answers(data: dict[str, Any]) -> bool:
    """True when an ebusd answers `info` at this address. Nothing is sent to the bus."""
    try:
        await EbusdClient(data[CONF_HOST], data[CONF_PORT]).info()
    except EbusdError:
        return False
    return True


class WeishauptConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()
            if await _answers(user_input):
                return self.async_create_entry(title="Weishaupt", data=user_input)
            errors["base"] = "cannot_connect"
        return self.async_show_form(step_id="user", data_schema=_schema(user_input or {}), errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()
            if await _answers(user_input):
                return self.async_update_reload_and_abort(
                    entry, unique_id=self.unique_id, data_updates=user_input)
            errors["base"] = "cannot_connect"
        return self.async_show_form(step_id="reconfigure", data_schema=_schema(user_input or dict(entry.data)),
                                    errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return WeishauptOptionsFlow()


def _seconds(minimum: int, maximum: int) -> selector.NumberSelector:
    return selector.NumberSelector(selector.NumberSelectorConfig(
        min=minimum, max=maximum, step=1, unit_of_measurement="s", mode=selector.NumberSelectorMode.BOX))


class WeishauptOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            data = {CONF_REQUEST_GAP: int(user_input[CONF_REQUEST_GAP]),
                    CONF_CYCLIC_INTERVAL: int(user_input[CONF_CYCLIC_INTERVAL]),
                    CONF_WRITES_ENABLED: bool(user_input.get(CONF_WRITES_ENABLED, False))}
            if user_input.get(CONF_TELEGRAM_DB):
                data[CONF_TELEGRAM_DB] = str(user_input[CONF_TELEGRAM_DB]).strip()
            return self.async_create_entry(data=data)
        options = self.config_entry.options
        schema = vol.Schema({
            vol.Required(CONF_REQUEST_GAP, default=options.get(CONF_REQUEST_GAP, DEFAULT_REQUEST_GAP)):
                _seconds(MIN_REQUEST_GAP, MAX_REQUEST_GAP),
            vol.Required(CONF_CYCLIC_INTERVAL, default=options.get(CONF_CYCLIC_INTERVAL, DEFAULT_CYCLIC_INTERVAL)):
                _seconds(MIN_CYCLIC_INTERVAL, MAX_CYCLIC_INTERVAL),
            vol.Required(CONF_WRITES_ENABLED, default=options.get(CONF_WRITES_ENABLED, False)): bool,
            vol.Optional(CONF_TELEGRAM_DB, default=options.get(CONF_TELEGRAM_DB, DEFAULT_TELEGRAM_DB)): str,
        })
        return self.async_show_form(step_id="init", data_schema=schema)
