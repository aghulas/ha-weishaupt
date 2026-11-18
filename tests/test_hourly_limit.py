"""The hourly write limit as an option of the config entry: default, accepted range, the guard honouring it, and a
reload (a new guard built from the changed options)."""
import ast
import importlib.util
import sys
import types
from pathlib import Path

import pytest

from weishaupt_core.const import CONF_MAX_WRITES_PER_HOUR, CONF_TELEGRAM_DB, CONF_WRITES_ENABLED
from weishaupt_core.guard import (MAX_PER_HOUR, MAX_PER_HOUR_RANGE, MIN_INTERVAL, WriteGuard, WriteRefused,
                                  guard_from_options, hourly_limit)

SRC = Path(__file__).resolve().parent.parent / "custom_components" / "weishaupt"


class Clock:
    def __init__(self, t=1_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


def fill(g, clock, count):
    """Record `count` accepted writes on distinct registers, a second apart."""
    for i in range(count):
        g.check(f"r{i}", 1, 0, 2, None)
        g.record(f"r{i}", None)
        clock.t += 1


def test_default_is_30_and_range_is_1_to_200():
    assert MAX_PER_HOUR == 30
    assert MAX_PER_HOUR_RANGE == (1, 200)
    assert hourly_limit(None) == 30


@pytest.mark.parametrize("value", [1, 2, 30, 199, 200, 200.0])
def test_accepted_values(value):
    assert hourly_limit(value) == int(value)


@pytest.mark.parametrize("value", [0, -1, 201, 1000, 2.5, "30", True, float("nan")])
def test_refused_values(value):
    with pytest.raises(ValueError):
        hourly_limit(value)
    with pytest.raises(ValueError):
        WriteGuard(True, max_per_hour=value)


def test_guard_default_limit_unchanged():
    clock = Clock()
    g = WriteGuard(True, clock=clock)
    assert g.max_per_hour == 30
    fill(g, clock, 30)
    with pytest.raises(WriteRefused) as err:
        g.check("next", 1, 0, 2, None)
    assert err.value.code == "hourly_limit" and err.value.placeholders == {"limit": "30"}


@pytest.mark.parametrize("limit", [1, 31, 200])
def test_guard_honours_the_option(limit):
    clock = Clock()
    g = guard_from_options({CONF_WRITES_ENABLED: True, CONF_MAX_WRITES_PER_HOUR: limit}, clock=clock)
    assert g.max_per_hour == limit
    fill(g, clock, limit)
    with pytest.raises(WriteRefused) as err:
        g.check("next", 1, 0, 2, None)
    assert err.value.placeholders == {"limit": str(limit)}
    with pytest.raises(WriteRefused):  # the clock broadcast counts against the same limit
        g.check_broadcast()
    clock.t += 3600 - limit + 1.5  # the oldest write leaves the sliding hour
    g.check("next", 1, 0, 2, None)
    g.check_broadcast()


def test_broadcasts_use_the_option_limit():
    clock = Clock()
    g = guard_from_options({CONF_WRITES_ENABLED: True, CONF_MAX_WRITES_PER_HOUR: 40}, clock=clock)
    for _ in range(39):
        g.check_broadcast()
        g.record_broadcast()
        clock.t += MIN_INTERVAL
    g.check("r", 1, 0, 2, None)
    g.record("r", None)
    clock.t += MIN_INTERVAL
    with pytest.raises(WriteRefused) as err:
        g.check_broadcast()
    assert err.value.code == "hourly_limit"


def test_other_checks_unchanged_with_a_high_limit():
    clock = Clock()
    g = guard_from_options({CONF_WRITES_ENABLED: True, CONF_MAX_WRITES_PER_HOUR: 200}, clock=clock)
    g.record("fs1:0500", None)
    with pytest.raises(WriteRefused) as err:  # still one write per register every 10 s
        g.check("fs1:0500", 21, 10, 26, None)
    assert err.value.code == "register_interval"
    with pytest.raises(WriteRefused) as err:  # bounds
        g.check("fs1:0800", 27, 10, 26, None)
    assert err.value.code == "out_of_bounds"
    with pytest.raises(WriteRefused) as err:  # ff without a readable log
        g.check("fs1:0800", 14, 10, 26, "ff")
    assert err.value.code == "log_unreadable"
    disabled = guard_from_options({CONF_MAX_WRITES_PER_HOUR: 200})
    with pytest.raises(WriteRefused) as err:
        disabled.check("fs1:0500", 21, 10, 26, None)
    assert err.value.code == "writes_disabled"


def test_entry_without_the_option_keeps_30():
    """Entries created by 0.1.1 and earlier have no such option."""
    g = guard_from_options({CONF_TELEGRAM_DB: "/share/ebusd/telegrams.db", CONF_WRITES_ENABLED: True})
    assert g.max_per_hour == 30 and g.enabled is True


@pytest.mark.parametrize("stored", [0, 500, "abc", 2.5])
def test_invalid_stored_option_falls_back_to_30(stored, caplog):
    g = guard_from_options({CONF_WRITES_ENABLED: True, CONF_MAX_WRITES_PER_HOUR: stored})
    assert g.max_per_hour == 30
    assert "max_writes_per_hour" in caplog.text


def test_reload_applies_a_new_value():
    """A change of options reloads the entry: the coordinator, and with it the guard, is built again from the new
    options. The old guard keeps its own limit; the new one honours the new value."""
    options = {CONF_WRITES_ENABLED: True}
    old = guard_from_options(options)
    options = {**options, CONF_MAX_WRITES_PER_HOUR: 200}
    new = guard_from_options(options)
    assert (old.max_per_hour, new.max_per_hour) == (30, 200)
    lowered = guard_from_options({**options, CONF_MAX_WRITES_PER_HOUR: 30})
    assert lowered.max_per_hour == 30


def test_options_update_reloads_the_entry_and_coordinator_builds_the_guard_from_options():
    """Static check of the wiring the suite cannot run without Home Assistant: setup registers an update listener
    that reloads the entry, and the coordinator builds its guard with guard_from_options(entry.options)."""
    init = ast.parse((SRC / "__init__.py").read_text())
    calls = {ast.unparse(node) for node in ast.walk(init) if isinstance(node, ast.Call)}
    assert "entry.add_update_listener(_async_reload)" in calls
    assert "hass.config_entries.async_reload(entry.entry_id)" in calls
    coordinator = (SRC / "coordinator.py").read_text()
    assert "self.guard = guard_from_options(entry.options)" in coordinator
    assert "WriteGuard(" not in coordinator


# --- options flow, with the few Home Assistant and voluptuous names it uses stubbed ---------------------------------

class Invalid(Exception):
    pass


def _voluptuous():
    vol = types.ModuleType("voluptuous")

    class Marker:
        def __init__(self, schema, default=None):
            self.schema, self.default = schema, default

    def coerce(kind):
        def run(value):
            try:
                return kind(value)
            except (TypeError, ValueError) as err:
                raise Invalid(str(err)) from err
        return run

    def range_(min=None, max=None):  # noqa: A002 - voluptuous' own argument names
        def run(value):
            if (min is not None and value < min) or (max is not None and value > max):
                raise Invalid(f"{value} not in [{min}, {max}]")
            return value
        run.min, run.max = min, max
        return run

    def all_(*validators):
        def run(value):
            for validator in validators:
                value = validator(value)
            return value
        run.validators = validators
        return run

    vol.Schema = lambda fields: fields
    vol.Required = Marker
    vol.Coerce, vol.Range, vol.All, vol.Invalid = coerce, range_, all_, Invalid
    return vol


def _homeassistant():
    modules = {name: types.ModuleType(name) for name in
               ("homeassistant", "homeassistant.config_entries", "homeassistant.const", "homeassistant.core")}

    class ConfigFlow:
        def __init_subclass__(cls, **kwargs):
            pass

    class OptionsFlow:
        def async_show_form(self, step_id, data_schema, errors=None):
            return {"type": "form", "step_id": step_id, "data_schema": data_schema}

        def async_create_entry(self, data):
            return {"type": "create_entry", "data": data}

    entries = modules["homeassistant.config_entries"]
    entries.ConfigFlow, entries.OptionsFlow, entries.ConfigEntry, entries.ConfigFlowResult = (
        ConfigFlow, OptionsFlow, object, dict)
    modules["homeassistant.const"].CONF_HOST, modules["homeassistant.const"].CONF_PORT = "host", "port"
    modules["homeassistant.core"].callback = lambda func: func
    return modules


@pytest.fixture
def options_flow(monkeypatch):
    monkeypatch.setitem(sys.modules, "voluptuous", _voluptuous())
    for name, module in _homeassistant().items():
        monkeypatch.setitem(sys.modules, name, module)
    spec = importlib.util.spec_from_file_location("weishaupt_core.config_flow", SRC / "config_flow.py")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)

    def make(options):
        flow = module.WeishauptOptionsFlow()
        flow.config_entry = types.SimpleNamespace(options=options)
        return flow
    return make


def _field(schema, key):
    marker = next(m for m in schema if m.schema == key)
    return marker, schema[marker]


def run(coro):
    import asyncio
    return asyncio.run(coro)


def test_options_form_offers_the_limit_with_default_30(options_flow):
    form = run(options_flow({CONF_TELEGRAM_DB: "/share/ebusd/telegrams.db", CONF_WRITES_ENABLED: False})
               .async_step_init())
    marker, validator = _field(form["data_schema"], CONF_MAX_WRITES_PER_HOUR)
    assert marker.default == 30
    assert [m.schema for m in form["data_schema"]] == [CONF_TELEGRAM_DB, CONF_WRITES_ENABLED, CONF_MAX_WRITES_PER_HOUR]


def test_options_form_shows_the_stored_value(options_flow):
    form = run(options_flow({CONF_MAX_WRITES_PER_HOUR: 200}).async_step_init())
    assert _field(form["data_schema"], CONF_MAX_WRITES_PER_HOUR)[0].default == 200


@pytest.mark.parametrize("value,accepted", [(1, 1), (30, 30), (200, 200), ("150", 150), (0, None), (201, None),
                                            (-5, None), ("x", None)])
def test_options_form_accepts_1_to_200(options_flow, value, accepted):
    form = run(options_flow({}).async_step_init())
    validator = _field(form["data_schema"], CONF_MAX_WRITES_PER_HOUR)[1]
    if accepted is None:
        with pytest.raises(Invalid):
            validator(value)
    else:
        assert validator(value) == accepted


def test_options_saved_as_entered(options_flow):
    entered = {CONF_TELEGRAM_DB: "/share/ebusd/telegrams.db", CONF_WRITES_ENABLED: True, CONF_MAX_WRITES_PER_HOUR: 200}
    result = run(options_flow({}).async_step_init(dict(entered)))
    assert result == {"type": "create_entry", "data": entered}
    assert guard_from_options(result["data"]).max_per_hour == 200
