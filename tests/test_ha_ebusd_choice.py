"""Which ebusd the entry uses: the build probed at every set-up, several endpoints, following the running one."""
from __future__ import annotations

from ha_common import make_entry, setup

NOTHING_TO_THE_BUS = ("info", "find")


def sent_to_bus(commands: list[tuple[float, str]]) -> list[str]:
    """Commands that could reach the bus: reads (`read`) and writes to a real circuit. `info`, `find` and the
    checksum probes (`write -c weishaupt-probe`, refused by ebusd before sending) never do."""
    return [text for _, text in commands
            if not text.startswith(NOTHING_TO_THE_BUS) and not text.startswith("write -c weishaupt-probe ")]


async def test_build_probed_with_writes_off(hass, fake):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    hub = entry.runtime_data
    assert hub.writer is None and hub.capability == "present"
    probes = [text for _, text in fake.commands if text.startswith("write")]
    assert len(probes) == 2 and all(text.startswith("write -c weishaupt-probe ") for text in probes)
    assert fake.writes == []  # nothing "sent"
    await hass.config_entries.async_unload(entry.entry_id)


async def test_stock_build_probed_with_writes_off(hass, fake):
    fake.runtime_checksum = False
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    assert entry.runtime_data.capability == "absent" and fake.writes == []
    await hass.config_entries.async_unload(entry.entry_id)


# ---- several endpoints ----------------------------------------------------------------------------------------

import pytest  # noqa: E402
from homeassistant.config_entries import ConfigEntryState  # noqa: E402
from homeassistant.const import CONF_HOST, CONF_PORT  # noqa: E402
from homeassistant.data_entry_flow import FlowResultType  # noqa: E402
from homeassistant.helpers import entity_registry as er  # noqa: E402
from homeassistant.helpers import issue_registry as ir  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.weishaupt.const import CONF_CYCLIC_INTERVAL, CONF_REQUEST_GAP, DOMAIN  # noqa: E402
from fake_ebusd import FakeEbusd  # noqa: E402
from ha_common import wait_until  # noqa: E402


def endpoint(fake, label: str, telegram_db: str = "/share/ebusd/telegrams.db") -> dict:
    return {CONF_HOST: "127.0.0.1", CONF_PORT: fake.port, "label": label, "addon": None, "telegram_db": telegram_db}


def entry_of(hass, *fakes, mode: str = "follow", in_use=None, **options) -> MockConfigEntry:
    """An entry of version 2.3 with one endpoint per simulated ebusd ("A", "B", …), the first in use."""
    in_use = in_use or fakes[0]
    entry = MockConfigEntry(
        domain=DOMAIN, version=2, minor_version=3, title="Weishaupt", unique_id=f"127.0.0.1:{fakes[0].port}",
        data={CONF_HOST: "127.0.0.1", CONF_PORT: in_use.port, "mode": mode,
              "endpoints": [endpoint(f, "AB"[i]) for i, f in enumerate(fakes)]},
        options={CONF_REQUEST_GAP: 0, CONF_CYCLIC_INTERVAL: 300} | options)
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def other(golden, socket_enabled):
    server = FakeEbusd(golden)
    await server.start()
    yield server
    await server.stop()


@pytest.fixture
def fast_retry(monkeypatch):
    """Retry a lost connection at once rather than after 30 s."""
    monkeypatch.setattr("custom_components.weishaupt.hub.CONNECTION_RETRY", 0.05)


def entity_ids(hass, entry) -> dict[str, str]:
    return {e.unique_id: e.entity_id for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)}


def issue(hass, kind: str, entry):
    return ir.async_get(hass).async_get_issue(DOMAIN, f"{kind}_{entry.entry_id}")


async def test_existing_entry_migrated_as_pinned(hass, fake, tmp_path):
    """An entry of 0.11 (2.2): its address becomes the one endpoint, pinned, with the telegram log of its options."""
    path = str(tmp_path / "telegrams.db")
    entry = make_entry(hass, fake, telegram_db=path)
    await setup(hass, entry)
    assert (entry.version, entry.minor_version) == (2, 3)
    assert entry.data == {CONF_HOST: "127.0.0.1", CONF_PORT: fake.port, "mode": "pinned",
                          "endpoints": [endpoint(fake, "ebusd", path)]}
    assert "telegram_db" not in entry.options and entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.endpoint.label == "ebusd"
    await hass.config_entries.async_unload(entry.entry_id)


async def test_follow_at_set_up_uses_the_running_one(hass, fake, other):
    port = fake.port
    await fake.stop()
    entry = entry_of(hass, fake, other)
    await setup(hass, entry)
    assert entry.state is ConfigEntryState.LOADED and entry.data[CONF_PORT] == other.port
    assert entry.runtime_data.endpoint.label == "B" and entry.unique_id == f"127.0.0.1:{port}"
    assert issue(hass, "ebusd_not_running", entry) is None
    await hass.config_entries.async_unload(entry.entry_id)


async def test_follow_prefers_a_signal_at_set_up(hass, fake, other):
    fake.signal = False
    entry = entry_of(hass, fake, other)
    await setup(hass, entry)
    assert entry.data[CONF_PORT] == other.port
    await hass.config_entries.async_unload(entry.entry_id)


async def test_switch_while_running(hass, fake, other, fast_retry):
    """The ebusd in use stops; after three failed connections the other one, which answers with a signal, is used:
    the entry reloads on it with the same entities, the write switch off, the build probed again on the new one,
    and nothing sent to its bus before the first pass."""
    other.runtime_checksum = False  # a stock ebusd
    entry = entry_of(hass, fake, other, writes_enabled=True)
    await setup(hass, entry)
    first = entry.runtime_data
    assert first.capability == "present"
    before = entity_ids(hass, entry)
    switch = before[f"{entry.entry_id}_writes"]
    await hass.services.async_call("switch", "turn_on", {"entity_id": switch}, blocking=True)
    assert hass.states.get(switch).state == "on"
    other.commands.clear()  # the survey of the set-up
    await fake.stop()
    await wait_until(lambda: entry.state is ConfigEntryState.LOADED and entry.runtime_data is not first
                     and entry.data[CONF_PORT] == other.port)
    await hass.async_block_till_done()
    hub = entry.runtime_data
    assert hub.endpoint.label == "B" and hub.capability == "absent"
    assert entity_ids(hass, entry) == before  # same registry entries: entity ids and history kept
    assert hass.states.get(switch).state == "off"
    await wait_until(lambda: any(text.startswith("read") for _, text in other.commands))  # the first pass has begun
    first_read = next(i for i, (_, text) in enumerate(other.commands) if text.startswith("read"))
    assert sent_to_bus(other.commands[:first_read]) == [] and other.writes == []
    assert issue(hass, "ebusd_not_running", entry) is None
    await hass.config_entries.async_unload(entry.entry_id)


async def test_no_switch_on_a_lost_signal(hass, fake, other, fast_retry, monkeypatch):
    """The ebusd in use answers without a signal (adapter or bus): the entry stays on it."""
    monkeypatch.setattr("custom_components.weishaupt.hub.NO_SIGNAL_PAUSE", 0.05)
    other.signal = False
    entry = entry_of(hass, fake, other)
    await setup(hass, entry)
    hub = entry.runtime_data
    fake.signal = False
    await wait_until(lambda: not hub.available)
    other.signal = True
    await wait_until(lambda: hub.statistics.no_signal >= 3)
    assert entry.runtime_data is hub and entry.data[CONF_PORT] == fake.port
    await hass.config_entries.async_unload(entry.entry_id)


async def test_two_with_a_signal(hass, fake, other):
    entry = entry_of(hass, fake, other, in_use=other)
    await setup(hass, entry)
    assert entry.data[CONF_PORT] == other.port  # kept, not switched
    found = issue(hass, "ebusd_several", entry)
    assert found is not None and found.translation_placeholders["labels"] == "A, B"
    await hass.config_entries.async_unload(entry.entry_id)


async def test_pinned_never_switches_and_says_so(hass, fake, other, fast_retry):
    entry = entry_of(hass, fake, other, mode="pinned")
    await setup(hass, entry)
    hub = entry.runtime_data
    await fake.stop()
    await wait_until(lambda: issue(hass, "ebusd_not_running", entry) is not None)
    assert entry.runtime_data is hub and entry.data[CONF_PORT] == fake.port and not hub.available
    found = issue(hass, "ebusd_not_running", entry)
    assert found.is_fixable and found.translation_key == "ebusd_not_running_fixable"
    assert "127.0.0.1" not in str(found.translation_placeholders)  # labels, never addresses
    assert "A: no answer" in found.translation_placeholders["endpoints"]
    assert "B: answers, signal" in found.translation_placeholders["endpoints"]
    await hass.config_entries.async_unload(entry.entry_id)


async def test_pinned_not_running_at_start_and_the_fix(hass, fake, other):
    """The pinned ebusd is stopped at start: the entry is not ready, the repair offers the one that answers; its
    flow changes the entry only, which then loads on that one."""
    from homeassistant.components.repairs import DOMAIN as REPAIRS
    from homeassistant.setup import async_setup_component
    assert await async_setup_component(hass, REPAIRS, {})
    entry = entry_of(hass, fake, other, mode="pinned")
    await fake.stop()
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    found = issue(hass, "ebusd_not_running", entry)
    assert found is not None and found.is_fixable
    from custom_components.weishaupt.repairs import async_create_fix_flow
    flow = await async_create_fix_flow(hass, found.issue_id, found.data)
    flow.hass = hass
    result = await flow.async_step_init()
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "choose"
    other.commands.clear()
    result = await flow.async_step_choose({"use": f"127.0.0.1:{other.port}"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await wait_until(lambda: entry.state is ConfigEntryState.LOADED)
    await hass.async_block_till_done()
    assert entry.data[CONF_PORT] == other.port and entry.data["mode"] == "pinned"
    assert issue(hass, "ebusd_not_running", entry) is None
    first_read = next((i for i, (_, text) in enumerate(other.commands) if text.startswith("read")),
                      len(other.commands))
    assert sent_to_bus(other.commands[:first_read]) == []
    await hass.config_entries.async_unload(entry.entry_id)


async def test_no_endpoint_answers(hass, fake, other, fast_retry):
    """Both stop: the entities are unavailable and the repair (not fixable) names each ebusd by its label."""
    entry = entry_of(hass, fake, other)
    await setup(hass, entry)
    hub = entry.runtime_data
    sensor = next(e for e in entity_ids(hass, entry).values()
                  if e.startswith("sensor.") and hass.states.get(e) is not None)
    await fake.stop()
    await other.stop()
    await wait_until(lambda: issue(hass, "ebusd_not_running", entry) is not None)
    found = issue(hass, "ebusd_not_running", entry)
    assert not found.is_fixable and found.translation_key == "ebusd_not_running"
    assert found.translation_placeholders["endpoints"] == "- A: no answer\n- B: no answer"
    await wait_until(lambda: hass.states.get(sensor).state == "unavailable")
    assert entry.runtime_data is hub
    await hass.config_entries.async_unload(entry.entry_id)


async def test_none_answers_at_start(hass, fake, other):
    entry = entry_of(hass, fake, other)
    await fake.stop()
    await other.stop()
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    found = issue(hass, "ebusd_not_running", entry)
    assert found is not None and not found.is_fixable


async def test_options_pin_and_follow(hass, fake, other):
    entry = entry_of(hass, fake, other)
    await setup(hass, entry)
    hub = entry.runtime_data
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "ebusd"})
    assert result["step_id"] == "ebusd"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"use": f"127.0.0.1:{other.port}"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await wait_until(lambda: entry.state is ConfigEntryState.LOADED and entry.runtime_data is not hub)
    await hass.async_block_till_done()
    assert entry.data["mode"] == "pinned" and entry.data[CONF_PORT] == other.port
    assert entry.runtime_data.endpoint.label == "B"
    await hass.config_entries.async_unload(entry.entry_id)


async def test_options_telegram_log_per_endpoint(hass, fake, other):
    entry = entry_of(hass, fake, other, writes_enabled=True)
    await setup(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "telegram_log"})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"endpoint": f"127.0.0.1:{other.port}"})
    assert result["step_id"] == "telegram_log_path"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"telegram_db": "/share/b.db"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    logs = {e[CONF_PORT]: e["telegram_db"] for e in entry.data["endpoints"]}
    assert logs == {fake.port: "/share/ebusd/telegrams.db", other.port: "/share/b.db"}
    await wait_until(lambda: entry.state is ConfigEntryState.LOADED)
    assert entry.runtime_data.writer.telegram_db == "/share/ebusd/telegrams.db"  # the log of the ebusd in use
    await hass.config_entries.async_unload(entry.entry_id)


async def test_another_version_behind_the_same_address_reloads(hass, fake):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    hub = entry.runtime_data
    fake.info = fake.info.replace(f"version: ebusd {hub.info.version}", "version: ebusd 26.2")
    hub._set_available(False, "test")
    hub._set_available(True)
    await wait_until(lambda: entry.state is ConfigEntryState.LOADED and entry.runtime_data is not hub)
    await hass.async_block_till_done()
    assert entry.runtime_data.info.version == "26.2"
    await hass.config_entries.async_unload(entry.entry_id)


async def test_diagnostics_name_no_endpoint(hass, fake, other):
    import json

    from custom_components.weishaupt.diagnostics import async_get_config_entry_diagnostics
    entry = entry_of(hass, fake, other)
    await setup(hass, entry)
    data = await async_get_config_entry_diagnostics(hass, entry)
    text = json.dumps(data)
    assert "127.0.0.1" not in text and "/share/ebusd/telegrams.db" not in text
    assert data["ebusd"]["endpoints"] == [{"label": "A", "addon": None}, {"label": "B", "addon": None}]
    assert data["ebusd"]["mode"] == "follow" and data["ebusd"]["endpoint_in_use"] == "A"
    await hass.config_entries.async_unload(entry.entry_id)
