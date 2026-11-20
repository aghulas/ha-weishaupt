"""Config flow (with its connection test), reconfiguration, options, migration of a 0.1 entry."""
import pytest
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.weishaupt.const import CONF_CYCLIC_INTERVAL, CONF_REQUEST_GAP, DOMAIN
from ha_common import make_entry, setup


async def test_user_flow(hass, fake):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "user"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "127.0.0.1", CONF_PORT: fake.port})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    endpoint = {CONF_HOST: "127.0.0.1", CONF_PORT: fake.port, "label": "ebusd", "addon": None,
                "telegram_db": "/share/ebusd/telegrams.db"}
    assert result["data"] == {CONF_HOST: "127.0.0.1", CONF_PORT: fake.port, "mode": "follow",
                              "endpoints": [endpoint]}
    assert result["result"].unique_id == f"127.0.0.1:{fake.port}"
    assert result["result"].state is ConfigEntryState.LOADED
    # the connection test asks `info` only: nothing goes to the bus
    assert fake.commands[0][1] == "info"


async def test_user_flow_cannot_connect_then_recovers(hass, fake):
    port = fake.port
    await fake.stop()
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_HOST: "127.0.0.1", CONF_PORT: port})
    assert result["type"] is FlowResultType.FORM and result["errors"] == {"base": "cannot_connect"}
    await fake.start()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "127.0.0.1", CONF_PORT: fake.port})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_something_that_is_not_ebusd(hass, fake):
    fake.info = "hello"
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "127.0.0.1", CONF_PORT: fake.port})
    assert result["errors"] == {"base": "cannot_connect"}


async def test_same_ebusd_twice(hass, fake):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "127.0.0.1", CONF_PORT: fake.port})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "already_configured"


async def test_reconfigure(hass, fake, golden):
    from fake_ebusd import FakeEbusd
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    other = FakeEbusd(golden)
    await other.start()
    try:
        result = await entry.start_reconfigure_flow(hass)
        assert result["step_id"] == "reconfigure"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "127.0.0.1", CONF_PORT: other.port})
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
        assert entry.data[CONF_PORT] == other.port and entry.unique_id == f"127.0.0.1:{other.port}"
        assert entry.state is ConfigEntryState.LOADED and other.commands
    finally:
        await hass.config_entries.async_unload(entry.entry_id)
        await other.stop()


async def test_options(hass, fake):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU and result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "settings"})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "settings"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_REQUEST_GAP: 5, CONF_CYCLIC_INTERVAL: 600})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    # the telegram log is set per ebusd since 0.12.0 (endpoints of the data), no longer among the options
    assert entry.options == {CONF_REQUEST_GAP: 5, CONF_CYCLIC_INTERVAL: 600, "writes_enabled": False,
                             "max_writes_per_hour": 30}
    hub = entry.runtime_data  # reloaded with the new options
    assert (hub.request_gap, hub.cyclic_interval) == (5, 600)


async def test_entry_of_version_0_1_is_migrated(hass, fake):
    """A 0.1 entry carried the options of the write path; they are dropped, the address is kept."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=1, title="Weishaupt", unique_id=f"127.0.0.1:{fake.port}",
        data={CONF_HOST: "127.0.0.1", CONF_PORT: fake.port},
        options={"telegram_db": "/share/ebusd/telegrams.db", "writes_enabled": True})
    entry.add_to_hass(hass)
    await setup(hass, entry)
    assert entry.version == 2 and entry.options == {}
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.request_gap == 2 and entry.runtime_data.cyclic_interval == 300
    await hass.config_entries.async_unload(entry.entry_id)


async def test_hourly_write_limit_option(hass, fake):
    """As in 0.1.2: 30 by default, 1 to 200, anything else refused by the form."""
    import voluptuous as vol
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "settings"})
    schema = result["data_schema"]
    assert schema({CONF_REQUEST_GAP: 2, CONF_CYCLIC_INTERVAL: 300})["max_writes_per_hour"] == 30
    for bad in (0, 201, "x"):
        with pytest.raises(vol.Invalid):
            schema({CONF_REQUEST_GAP: 2, CONF_CYCLIC_INTERVAL: 300, "max_writes_per_hour": bad})
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_REQUEST_GAP: 2, CONF_CYCLIC_INTERVAL: 300, "max_writes_per_hour": 200})
    await hass.async_block_till_done()
    assert entry.options["max_writes_per_hour"] == 200


# ---- ebusd add-ons of Home Assistant OS (0.12.0) ------------------------------------------------------------------

from dataclasses import dataclass  # noqa: E402
from unittest.mock import patch  # noqa: E402

from custom_components.weishaupt.supervisor import Addon, is_ebusd  # noqa: E402


@dataclass(frozen=True)
class LocalAddon(Addon):
    """An add-on whose ebusd is a simulated one on this machine."""

    @property
    def host(self) -> str:
        return "127.0.0.1"


def addons(*items):
    return patch("custom_components.weishaupt.config_flow.ebusd_addons", return_value=list(items))


def test_which_add_ons_are_ebusd():
    assert is_ebusd("ebusd") and is_ebusd("2ad9b828_ebusd") and is_ebusd("09e0ce7c_ebusd_next")
    assert not is_ebusd("core_mosquitto") and not is_ebusd("a0d7b954_ebusdx") and not is_ebusd("ebusd-mcp")


async def test_user_flow_with_add_ons(hass, fake, golden):
    from fake_ebusd import FakeEbusd
    stopped = FakeEbusd(golden)
    await stopped.start()
    await stopped.stop()  # installed, not started: stored without being asked
    running = LocalAddon("abc_ebusd", "eBUSd (Weishaupt CRC)", "started", fake.port)
    idle = LocalAddon("def_ebusd", "eBUSd", "stopped", stopped.port)
    with addons(running, idle):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        assert result["type"] is FlowResultType.FORM and result["step_id"] == "addons"
        assert result["data_schema"]({})["addons"] == ["abc_ebusd"]  # the started ones by default
        bad = await hass.config_entries.flow.async_configure(result["flow_id"], {"addons": []})
        assert bad["errors"] == {"base": "no_endpoint"}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"addons": ["abc_ebusd", "def_ebusd"]})
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    data = result["data"]
    assert data["mode"] == "follow" and data[CONF_PORT] == fake.port
    assert [(e["label"], e["addon"], e[CONF_PORT]) for e in data["endpoints"]] == [
        ("eBUSd (Weishaupt CRC)", "abc_ebusd", fake.port), ("eBUSd", "def_ebusd", stopped.port)]
    assert [c for _, c in stopped.commands] == []
    entry = result["result"]
    assert entry.state is ConfigEntryState.LOADED
    await hass.config_entries.async_unload(entry.entry_id)


async def test_user_flow_with_add_ons_none_running(hass, fake):
    port = fake.port
    await fake.stop()
    with addons(LocalAddon("abc_ebusd", "eBUSd", "started", port)):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"addons": ["abc_ebusd"]})
    assert result["errors"] == {"base": "cannot_connect"}


async def test_reconfigure_with_add_ons_keeps_the_entry(hass, fake, golden):
    from fake_ebusd import FakeEbusd
    from homeassistant.helpers import entity_registry as er
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    before = {e.unique_id: e.entity_id for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)}
    other = FakeEbusd(golden)
    await other.start()
    try:
        with addons(LocalAddon("abc_ebusd", "eBUSd", "started", other.port)):
            result = await entry.start_reconfigure_flow(hass)
            assert result["step_id"] == "reconfigure_addons"
            # the address typed before stays as the other ebusd; the add-on is added
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {"addons": ["abc_ebusd"], CONF_HOST: "127.0.0.1", CONF_PORT: fake.port})
            await hass.async_block_till_done()
        assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
        assert entry.data[CONF_PORT] == fake.port  # the one in use answers: kept
        assert [e["label"] for e in entry.data["endpoints"]] == ["eBUSd", "ebusd"]
        assert entry.data["mode"] == "pinned"  # migrated as pinned, unchanged by the list
        after = {e.unique_id: e.entity_id for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)}
        assert after == before
    finally:
        await hass.config_entries.async_unload(entry.entry_id)
        await other.stop()


async def test_endpoint_of_another_entry_refused(hass, fake):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    with addons(LocalAddon("abc_ebusd", "eBUSd", "started", fake.port)):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"addons": ["abc_ebusd"]})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "already_configured"
    await hass.config_entries.async_unload(entry.entry_id)
