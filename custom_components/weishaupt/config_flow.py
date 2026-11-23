"""Configuration: the ebusd endpoints (on Home Assistant OS, the ebusd add-ons from the Supervisor's list, and one
typed by hand), with a connection test (`info` only), and how to pick among them (follow the running one, or pin
one); options: the load put on the bus, writes (off unless enabled here; the write switch then turns them on and
off), which ebusd to use, and the telegram log of each ebusd.

The integration registers a custom panel with `config_panel_domain`, so the entry's *Configure* button opens the
panel, not the options flow — which then has no button of its own. Reconfigure (⋮ menu) is therefore the UI path
to the options: it opens a menu (*ebusd*, *Bus load and writes*, *Telegram log of each ebusd*) whose steps reuse
the schema and the persistence of the options steps below. The options flow itself is kept unchanged: it is driven
by the WebSocket API and by the tests, and the two paths write the same data and options."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ALLOW_STOCK_WRITES,
    CONF_CYCLIC_INTERVAL,
    CONF_MAX_WRITES_PER_HOUR,
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
from .endpoints import (
    CONF_ENDPOINTS,
    MODE_FOLLOW,
    MODE_PINNED,
    Endpoint,
    apply_choice,
    choose,
    current,
    endpoints_of,
    manual_label,
    mode_of,
    survey,
    use,
)
from .guard import MAX_PER_HOUR, MAX_PER_HOUR_RANGE
from .supervisor import Addon, ebusd_addons

CONF_ADDONS = "addons"
CONF_USE = "use"
CONF_LOG_ENDPOINT = "endpoint"


def _settings_schema(options: Any) -> vol.Schema:
    """The bus load and writes form, from the current options. Shared by the options step and reconfigure."""
    return vol.Schema({
        vol.Required(CONF_REQUEST_GAP, default=options.get(CONF_REQUEST_GAP, DEFAULT_REQUEST_GAP)):
            _seconds(MIN_REQUEST_GAP, MAX_REQUEST_GAP),
        vol.Required(CONF_CYCLIC_INTERVAL, default=options.get(CONF_CYCLIC_INTERVAL, DEFAULT_CYCLIC_INTERVAL)):
            _seconds(MIN_CYCLIC_INTERVAL, MAX_CYCLIC_INTERVAL),
        vol.Required(CONF_WRITES_ENABLED, default=options.get(CONF_WRITES_ENABLED, False)): bool,
        vol.Required(CONF_ALLOW_STOCK_WRITES, default=options.get(CONF_ALLOW_STOCK_WRITES, False)): bool,
        vol.Required(CONF_MAX_WRITES_PER_HOUR, default=options.get(CONF_MAX_WRITES_PER_HOUR, MAX_PER_HOUR)):
            vol.All(vol.Coerce(int), vol.Range(min=MAX_PER_HOUR_RANGE[0], max=MAX_PER_HOUR_RANGE[1])),
    })


def _settings_data(user_input: dict[str, Any]) -> dict[str, Any]:
    """The options a submitted bus-load form holds. Shared by the options step and reconfigure."""
    return {CONF_REQUEST_GAP: int(user_input[CONF_REQUEST_GAP]),
            CONF_CYCLIC_INTERVAL: int(user_input[CONF_CYCLIC_INTERVAL]),
            CONF_WRITES_ENABLED: bool(user_input.get(CONF_WRITES_ENABLED, False)),
            CONF_ALLOW_STOCK_WRITES: bool(user_input.get(CONF_ALLOW_STOCK_WRITES, False)),
            CONF_MAX_WRITES_PER_HOUR: int(user_input.get(CONF_MAX_WRITES_PER_HOUR, MAX_PER_HOUR))}


def _telegram_db_data(data: dict[str, Any], endpoint_key: str, path: str) -> dict[str, Any]:
    """The entry data with the telegram log of one endpoint set. Shared by the options step and reconfigure."""
    known = endpoints_of(data)
    path = path.strip() or DEFAULT_TELEGRAM_DB
    changed = [Endpoint(e.host, e.port, e.label, e.addon, path) if e.key == endpoint_key else e for e in known]
    return {**data, CONF_ENDPOINTS: [e.as_dict() for e in changed]}


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema({
        vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, vol.UNDEFINED)): str,
        vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)),
    })


def _addon_schema(addons: list[Addon], chosen: list[str], manual: Endpoint | None) -> vol.Schema:
    """The ebusd add-ons of Home Assistant OS to keep, and one ebusd typed by hand (optional)."""
    options = [selector.SelectOptionDict(value=a.slug, label=f"{a.name} ({a.host}, {a.state or '?'})") for a in addons]
    return vol.Schema({
        vol.Optional(CONF_ADDONS, default=chosen): selector.SelectSelector(selector.SelectSelectorConfig(
            options=options, multiple=True, mode=selector.SelectSelectorMode.LIST)),
        vol.Optional(CONF_HOST, description={"suggested_value": manual.host if manual else None}): str,
        vol.Optional(CONF_PORT, default=manual.port if manual else DEFAULT_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)),
    })


async def _answers(data: dict[str, Any]) -> bool:
    """True when an ebusd answers `info` at this address. Nothing is sent to the bus."""
    try:
        await EbusdClient(data[CONF_HOST], data[CONF_PORT]).info()
    except EbusdError:
        return False
    return True


def _taken(hass, keys: set[str], own_entry_id: str | None = None) -> bool:
    """Whether another entry already has one of these endpoints."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.entry_id == own_entry_id or CONF_HOST not in entry.data:
            continue
        if keys & {e.key for e in endpoints_of(dict(entry.data))}:
            return True
    return False


def _endpoints_from_form(user_input: dict[str, Any], addons: list[Addon], previous: list[Endpoint]) -> list[Endpoint]:
    """The endpoints a submitted form asks for: the add-ons ticked, then the one typed by hand. What an endpoint of
    the same address had (its telegram log, its label) is kept."""
    before = {e.key: e for e in previous}
    found: list[Endpoint] = []
    by_slug = {a.slug: a for a in addons}
    for slug in user_input.get(CONF_ADDONS) or []:
        addon = by_slug.get(slug)
        if addon is None:
            continue
        old = before.get(f"{addon.host}:{addon.port}")
        found.append(Endpoint(addon.host, addon.port, addon.name, addon.slug,
                              old.telegram_db if old else DEFAULT_TELEGRAM_DB))
    host = str(user_input.get(CONF_HOST) or "").strip()
    if host:
        port = int(user_input.get(CONF_PORT) or DEFAULT_PORT)
        key = f"{host}:{port}"
        if key not in {e.key for e in found}:
            old = before.get(key)
            label = old.label if old and not old.addon else manual_label(found)
            found.append(Endpoint(host, port, label, None, old.telegram_db if old else DEFAULT_TELEGRAM_DB))
    return found


async def _pick(candidates: list[Endpoint], in_use: Endpoint | None,
                stopped: set[str]) -> tuple[Endpoint | None, list[Endpoint]]:
    """The endpoint to use among those of a form, asked `info` (stopped add-ons are not asked: they are stored
    untested)."""
    asked = [e for e in candidates if e.addon not in stopped]
    surveys = await survey(asked)
    return choose(in_use or (asked[0] if asked else candidates[0]), surveys)


class WeishauptConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 2
    # 2.1: 0.3.0b2 and before; 2.2 enables the numbers 0.3.0b2 created disabled; 2.3 (0.12.0): ebusd endpoints
    MINOR_VERSION = 3

    _candidates: list[Endpoint] = []  # the endpoints a reconfigure chose, carried to its mode step
    _log_endpoint: str | None = None  # the endpoint a reconfigure telegram-log step chose, carried to its path step

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        addons = ebusd_addons(self.hass)
        if not addons:
            return await self._step_manual(user_input)
        errors = {}
        if user_input is not None:
            candidates = _endpoints_from_form(user_input, addons, [])
            if not candidates:
                errors["base"] = "no_endpoint"
            elif _taken(self.hass, {e.key for e in candidates}):
                return self.async_abort(reason="already_configured")
            else:
                stopped = {a.slug for a in addons if not a.started}
                chosen, _ = await _pick(candidates, None, stopped)
                if chosen is not None:
                    await self.async_set_unique_id(chosen.key)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title="Weishaupt", data=use(
                        {CONF_HOST: chosen.host, CONF_PORT: chosen.port,
                         CONF_ENDPOINTS: [e.as_dict() for e in candidates]}, chosen, MODE_FOLLOW))
                errors["base"] = "cannot_connect"
        chosen = (user_input or {}).get(CONF_ADDONS, [a.slug for a in addons if a.started])
        return self.async_show_form(step_id="addons", data_schema=_addon_schema(addons, chosen, None), errors=errors)

    async def async_step_addons(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self.async_step_user(user_input)

    async def _step_manual(self, user_input: dict[str, Any] | None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()
            if _taken(self.hass, {self.unique_id}):
                return self.async_abort(reason="already_configured")
            if await _answers(user_input):
                endpoint = Endpoint(user_input[CONF_HOST], int(user_input[CONF_PORT]), "ebusd")
                return self.async_create_entry(title="Weishaupt", data=use(
                    {**user_input, CONF_ENDPOINTS: [endpoint.as_dict()]}, endpoint, MODE_FOLLOW))
            errors["base"] = "cannot_connect"
        return self.async_show_form(step_id="user", data_schema=_schema(user_input or {}), errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """The entry's menu, the UI path to the options the panel does not expose: the endpoints and their mode,
        the bus load and writes, the telegram log of each ebusd."""
        return self.async_show_menu(step_id="reconfigure", menu_options=["endpoints", "settings", "telegram_log"])

    async def async_step_endpoints(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        data = dict(entry.data)
        previous = endpoints_of(data)
        addons = ebusd_addons(self.hass)
        errors = {}
        if not addons:  # one address, as before 0.12.0: the endpoint in use moves
            if user_input is not None:
                key = f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                await self.async_set_unique_id(key)
                if _taken(self.hass, {key}, entry.entry_id):  # another entry has it; keeping the own address (to
                    return self.async_abort(reason="already_configured")  # change only the mode) is allowed
                if await _answers(user_input):
                    old = current(data)
                    moved = Endpoint(user_input[CONF_HOST], int(user_input[CONF_PORT]), old.label, old.addon,
                                     old.telegram_db)
                    rest = [e for e in previous if e.key not in (old.key, moved.key)]
                    self._candidates = [moved, *rest]
                    return await self.async_step_reconfigure_use()
                errors["base"] = "cannot_connect"
            return self.async_show_form(step_id="endpoints", data_schema=_schema(user_input or data), errors=errors)
        if user_input is not None:
            candidates = _endpoints_from_form(user_input, addons, previous)
            if not candidates:
                errors["base"] = "no_endpoint"
            elif _taken(self.hass, {e.key for e in candidates}, entry.entry_id):
                return self.async_abort(reason="already_configured")
            else:
                self._candidates = candidates
                return await self.async_step_reconfigure_use()
        chosen = (user_input or {}).get(CONF_ADDONS, [e.addon for e in previous if e.addon])
        manual = next((e for e in previous if not e.addon), None)
        return self.async_show_form(step_id="reconfigure_addons", data_schema=_addon_schema(addons, chosen, manual),
                                    errors=errors)

    async def async_step_reconfigure_addons(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self.async_step_endpoints(user_input)

    async def async_step_reconfigure_use(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """After the endpoints: follow the running one, or pin one. Changing the mode (or the endpoints) reloads
        the entry — entities and history kept, writes off, the build probed again. Nothing reaches the bus: `info`
        only, and pinning asks nothing at all."""
        entry = self._get_reconfigure_entry()
        data = dict(entry.data)
        candidates = self._candidates
        errors = {}
        if user_input is not None:
            base = {**data, CONF_ENDPOINTS: [e.as_dict() for e in candidates]}
            if user_input[CONF_USE] == MODE_FOLLOW:
                stopped = {a.slug for a in ebusd_addons(self.hass) if not a.started}
                in_use = next((e for e in candidates if e.key == current(data).key), None)
                chosen, _ = await _pick(candidates, in_use, stopped)
                if chosen is not None:
                    new = use({**base, CONF_HOST: chosen.host, CONF_PORT: chosen.port}, chosen, MODE_FOLLOW)
                    return self.async_update_reload_and_abort(entry, unique_id=chosen.key, data=new)
                errors["base"] = "cannot_connect"
            else:
                pinned = next(e for e in candidates if e.key == user_input[CONF_USE])
                new = use({**base, CONF_HOST: pinned.host, CONF_PORT: pinned.port}, pinned, MODE_PINNED)
                return self.async_update_reload_and_abort(entry, unique_id=pinned.key, data=new)
        keys = {e.key for e in candidates}
        default = MODE_FOLLOW if mode_of(data) == MODE_FOLLOW or current(data).key not in keys else current(data).key
        options = [selector.SelectOptionDict(value=MODE_FOLLOW, label="follow")] + [
            selector.SelectOptionDict(value=e.key, label=f"{e.label} ({e.key})") for e in candidates]
        schema = vol.Schema({vol.Required(CONF_USE, default=default): selector.SelectSelector(
            selector.SelectSelectorConfig(options=options, translation_key="ebusd_choice"))})
        return self.async_show_form(step_id="reconfigure_use", data_schema=schema, errors=errors)

    async def async_step_settings(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Bus load and writes, from the reconfigure menu: the options the panel does not expose. Changing them
        reloads the entry (its update listener), as the options step does."""
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            return self.async_update_reload_and_abort(entry, options=_settings_data(user_input))
        return self.async_show_form(step_id="settings", data_schema=_settings_schema(entry.options))

    async def async_step_telegram_log(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Which ebusd's telegram log to set: asked only when there are several."""
        entry = self._get_reconfigure_entry()
        known = endpoints_of(dict(entry.data))
        if user_input is not None or len(known) == 1:
            self._log_endpoint = user_input[CONF_LOG_ENDPOINT] if user_input is not None else known[0].key
            return await self.async_step_telegram_log_path()
        options = [selector.SelectOptionDict(value=e.key, label=f"{e.label} ({e.key})") for e in known]
        schema = vol.Schema({vol.Required(CONF_LOG_ENDPOINT, default=current(dict(entry.data)).key):
                             selector.SelectSelector(selector.SelectSelectorConfig(options=options))})
        return self.async_show_form(step_id="telegram_log", data_schema=schema)

    async def async_step_telegram_log_path(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        data = dict(entry.data)
        endpoint = next(e for e in endpoints_of(data) if e.key == self._log_endpoint)
        if user_input is not None:
            new = _telegram_db_data(data, endpoint.key, str(user_input.get(CONF_TELEGRAM_DB) or ""))
            return self.async_update_reload_and_abort(entry, data=new)
        schema = vol.Schema({vol.Required(CONF_TELEGRAM_DB, default=endpoint.telegram_db): str})
        return self.async_show_form(step_id="telegram_log_path", data_schema=schema,
                                    description_placeholders={"label": endpoint.label})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return WeishauptOptionsFlow()


def _seconds(minimum: int, maximum: int) -> selector.NumberSelector:
    return selector.NumberSelector(selector.NumberSelectorConfig(
        min=minimum, max=maximum, step=1, unit_of_measurement="s", mode=selector.NumberSelectorMode.BOX))


class WeishauptOptionsFlow(OptionsFlow):
    """A menu: load on the bus and writes; which ebusd; the telegram log of each ebusd."""

    _log_endpoint: str | None = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(step_id="init", menu_options=["settings", "ebusd", "telegram_log"])

    async def async_step_settings(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=_settings_data(user_input))
        return self.async_show_form(step_id="settings", data_schema=_settings_schema(self.config_entry.options))

    async def async_step_ebusd(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Follow the running ebusd, or pin one. The entry reloads with it: writes off, the build probed again."""
        data = dict(self.config_entry.data)
        if user_input is not None:
            apply_choice(self.hass, self.config_entry, user_input[CONF_USE])
            return self.async_create_entry(data=dict(self.config_entry.options))
        options = [selector.SelectOptionDict(value=MODE_FOLLOW, label="follow")] + [
            selector.SelectOptionDict(value=e.key, label=f"{e.label} ({e.key})") for e in endpoints_of(data)]
        default = MODE_FOLLOW if mode_of(data) == MODE_FOLLOW else current(data).key
        schema = vol.Schema({vol.Required(CONF_USE, default=default): selector.SelectSelector(
            selector.SelectSelectorConfig(options=options, translation_key="ebusd_choice"))})
        return self.async_show_form(step_id="ebusd", data_schema=schema,
                                    description_placeholders={"label": current(data).label})

    async def async_step_telegram_log(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Which ebusd's telegram log to set: asked only when there are several."""
        data = dict(self.config_entry.data)
        known = endpoints_of(data)
        if user_input is not None or len(known) == 1:
            self._log_endpoint = user_input[CONF_LOG_ENDPOINT] if user_input is not None else known[0].key
            return await self.async_step_telegram_log_path()
        options = [selector.SelectOptionDict(value=e.key, label=f"{e.label} ({e.key})") for e in known]
        schema = vol.Schema({vol.Required(CONF_LOG_ENDPOINT, default=current(data).key): selector.SelectSelector(
            selector.SelectSelectorConfig(options=options))})
        return self.async_show_form(step_id="telegram_log", data_schema=schema)

    async def async_step_telegram_log_path(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        data = dict(self.config_entry.data)
        endpoint = next(e for e in endpoints_of(data) if e.key == self._log_endpoint)
        if user_input is not None:
            new = _telegram_db_data(data, endpoint.key, str(user_input.get(CONF_TELEGRAM_DB) or ""))
            self.hass.config_entries.async_update_entry(self.config_entry, data=new)
            return self.async_create_entry(data=dict(self.config_entry.options))
        schema = vol.Schema({vol.Required(CONF_TELEGRAM_DB, default=endpoint.telegram_db): str})
        return self.async_show_form(step_id="telegram_log_path", data_schema=schema,
                                    description_placeholders={"label": endpoint.label})
