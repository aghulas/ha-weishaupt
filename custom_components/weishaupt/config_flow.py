"""Configuration: ebusd address; options: telegram log and writes (disabled by default)."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

from .const import CONF_TELEGRAM_DB, CONF_WRITES_ENABLED, DEFAULT_PORT, DEFAULT_TELEGRAM_DB, DOMAIN
from .protocol import EbusdClient, EbusdError, read_command


class WeishauptConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()
            try:
                # read the normal room setpoint of KA: proves ebusd answers and accepts hex commands
                await EbusdClient(user_input[CONF_HOST], user_input[CONF_PORT]).command(read_command("15", ["0500"]))
            except (OSError, TimeoutError, EbusdError):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="Weishaupt", data=user_input,
                                               options={CONF_TELEGRAM_DB: DEFAULT_TELEGRAM_DB,
                                                        CONF_WRITES_ENABLED: False})
        schema = vol.Schema({vol.Required(CONF_HOST): str, vol.Required(CONF_PORT, default=DEFAULT_PORT): int})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return WeishauptOptionsFlow()


class WeishauptOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        options = self.config_entry.options
        schema = vol.Schema({
            vol.Required(CONF_TELEGRAM_DB, default=options.get(CONF_TELEGRAM_DB, DEFAULT_TELEGRAM_DB)): str,
            vol.Required(CONF_WRITES_ENABLED, default=options.get(CONF_WRITES_ENABLED, False)): bool,
        })
        return self.async_show_form(step_id="init", data_schema=schema)
