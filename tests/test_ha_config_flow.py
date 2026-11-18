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
    assert result["data"] == {CONF_HOST: "127.0.0.1", CONF_PORT: fake.port}
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
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_REQUEST_GAP: 5, CONF_CYCLIC_INTERVAL: 600})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_REQUEST_GAP: 5, CONF_CYCLIC_INTERVAL: 600, "writes_enabled": False,
                             "telegram_db": "/share/ebusd/telegrams.db", "max_writes_per_hour": 30}
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
    schema = result["data_schema"]
    assert schema({CONF_REQUEST_GAP: 2, CONF_CYCLIC_INTERVAL: 300})["max_writes_per_hour"] == 30
    for bad in (0, 201, "x"):
        with pytest.raises(vol.Invalid):
            schema({CONF_REQUEST_GAP: 2, CONF_CYCLIC_INTERVAL: 300, "max_writes_per_hour": bad})
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_REQUEST_GAP: 2, CONF_CYCLIC_INTERVAL: 300, "max_writes_per_hour": 200})
    await hass.async_block_till_done()
    assert entry.options["max_writes_per_hour"] == 200
