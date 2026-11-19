"""The paced reader: what is asked from ebusd, in which order, how far apart — and that nothing is written."""
import asyncio
import re

from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.helpers import entity_registry as er

from custom_components.weishaupt import hub as hub_module
from custom_components.weishaupt.const import DOMAIN
from ha_common import make_entry, settled, setup, state_of, wait_until


def _message(command: str) -> str:
    match = re.match(r"read -m \d+ -c (\S+) (\S+)$", command)
    return f"{match.group(1)}/{match.group(2)}"


async def test_only_reading_commands_reach_ebusd(hass, fake):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    hub = entry.runtime_data
    verbs = {command.split()[0] for _, command in fake.commands}
    assert verbs == {"info", "find", "read"}
    assert all(re.fullmatch(r"info|find -f -c \w+|read -m \d+ -c \w+ \w+", c) for _, c in fake.commands)
    assert fake.max_active == 1  # one command at a time
    assert len(fake.reads_of("info")) == 1 and len(fake.reads_of("find")) == 10
    # each message that an enabled entity shows was asked once, no other
    asked = [_message(c) for _, c in fake.reads_of()]
    assert len(asked) == len(set(asked))
    registry = er.async_get(hass)
    enabled = {e.unique_id.removeprefix(f"{entry.entry_id}_") for e in
               er.async_entries_for_config_entry(registry, entry.entry_id) if not e.disabled_by}
    expected = {e.message.key for e in hub.model.value_entities if e.key in enabled}
    for group in hub.model.group_entities:
        if group.key in enabled:
            expected |= set(group.group.members)
    expected |= {"bc1/FaultHistoryPointer", "bc2/FaultHistoryPointer"}  # read for the fault history sensors
    assert set(asked) == expected
    # disabled by default, so never requested: per-fault counters, programs a room unit only stores, the clock
    assert not [k for k in asked if "FaultCounters" in k or "Program" in k or k.startswith("em1/System")
                or hub.model.messages[k].kind == "setting"]
    assert len(asked) == 69 and hub.statistics.bus_requests == 61  # 8 passive messages come from the cache
    assert hub.statistics.bus_requests + hub.statistics.cache_reads == len(asked)


async def test_order_and_max_age(hass, fake, entity_registry_enabled_by_default):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    hub = entry.runtime_data
    commands = [c for _, c in fake.reads_of()]
    ages = {_message(c): int(c.split()[2]) for c in commands}
    order = [hub.interval(hub.model.messages[_message(c)]) for c in commands]
    # passive messages first, then live values, then counters, settings and at last the weekly programs
    assert order == sorted(order)
    assert sorted(set(order)) == [30, 300, 3600, 6 * 3600, 24 * 3600]
    # the age ebusd may answer from its cache: the interval of the class; passive messages are never requested
    assert ages["ka/Boiler1Status"] == 900 and ages["bc1/Temperatures"] == 300
    assert ages["bc1/Counters"] == 3600 and ages["bc1/BurnerServiceHours"] == 3600
    assert ages["ka/BlockingTime"] == 6 * 3600 and ages["fs1/HCProgram1Mon1"] == 24 * 3600


async def test_cyclic_interval_option(hass, fake):
    entry = make_entry(hass, fake, cyclic_interval=120)
    await setup(hass, entry)
    await settled(hass, entry)
    assert "read -m 120 -c bc1 Temperatures" in [c for _, c in fake.reads_of()]


async def test_requests_are_spaced(hass, fake):
    """Never two bus requests closer than the gap; reads of passive messages (ebusd's cache) do not wait."""
    gap = 0.15
    entry = make_entry(hass, fake, gap=gap)
    await setup(hass, entry)
    hub = entry.runtime_data
    await wait_until(lambda: hub.statistics.bus_requests >= 12, timeout=10)
    reads = fake.reads_of()
    passive = [(t, c) for t, c in reads if hub.model.messages[_message(c)].passive]
    bus = [(t, c) for t, c in reads if not hub.model.messages[_message(c)].passive]
    assert len(passive) == 8 and passive[-1][0] - passive[0][0] < gap  # all at once, before the first request
    gaps = [b[0] - a[0] for a, b in zip(bus, bus[1:])]
    assert min(gaps) >= gap * 0.9
    assert max(gaps) < gap * 3  # and no slower than asked while messages are due


async def test_a_message_is_read_again_when_due(hass, fake, monkeypatch):
    monkeypatch.setattr(hub_module, "PASSIVE_INTERVAL", 0.2)
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    assert state_of(hass, entry, "ka/Boiler1Power/currentload").state == "54"
    fake.reads["ka/Boiler1Power"] = "61;23;100"
    await wait_until(lambda: state_of(hass, entry, "ka/Boiler1Power/currentload").state == "61")
    # a live value is not asked again before its interval
    assert len([c for _, c in fake.reads_of() if c.endswith("bc1 Temperatures")]) == 1


async def test_no_signal_then_back(hass, fake, monkeypatch):
    monkeypatch.setattr(hub_module, "NO_SIGNAL_PAUSE", 0.3)
    fake.signal = False
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    hub = entry.runtime_data
    await wait_until(lambda: not hub.available)
    await hass.async_block_till_done()
    assert state_of(hass, entry, "bc1/SupplyTemp/value").state == STATE_UNAVAILABLE
    before = len(fake.reads_of())
    await asyncio.sleep(0.15)
    assert len(fake.reads_of()) - before <= 1  # no request while there is no signal
    fake.signal = True
    await wait_until(lambda: hub.available)
    await settled(hass, entry)
    assert state_of(hass, entry, "bc1/SupplyTemp/value").state == "50.0"
    assert hub.statistics.no_signal >= 1


async def test_ebusd_lost_then_back(hass, fake, monkeypatch, caplog):
    monkeypatch.setattr(hub_module, "CONNECTION_RETRY", 0.2)
    monkeypatch.setattr(hub_module, "PASSIVE_INTERVAL", 0.2)
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    hub = entry.runtime_data
    port = fake.port
    await fake.stop()
    await wait_until(lambda: not hub.available)
    await hass.async_block_till_done()
    assert state_of(hass, entry, "ka/Boiler1Power/currentload").state == STATE_UNAVAILABLE
    assert caplog.text.count("ebusd cannot be reached") == 1  # logged once, not at every attempt
    fake._server = await asyncio.start_server(fake._handle, "127.0.0.1", port)
    await wait_until(lambda: hub.available)
    await hass.async_block_till_done()
    assert state_of(hass, entry, "ka/Boiler1Power/currentload").state == "54"
    assert "ebusd answers again" in caplog.text


async def test_a_failing_message_does_not_stop_the_others(hass, fake, monkeypatch):
    monkeypatch.setattr(hub_module, "RETRY_INTERVAL", 0.05)
    fake.reads["bc1/SupplyTemp"] = "ERR: read timeout"
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    hub = entry.runtime_data
    await wait_until(lambda: hub._failures.get("bc1/SupplyTemp", 0) >= 3)
    await wait_until(lambda: "bc1/ReturnTemp" in hub.readings and "bc1/Counters" in hub.readings)
    await hass.async_block_till_done()
    assert hub.available
    assert state_of(hass, entry, "bc1/ReturnTemp/value").state == "57.0"
    assert state_of(hass, entry, "bc1/SupplyTemp/value").state == "unknown"
    assert hub.statistics.last_error.startswith("bc1/SupplyTemp")


async def test_read_only_unless_writes_are_enabled(hass, fake):
    """Without the write option: no entity that sets a value, no action, and no write command of any form sent to
    ebusd, not even the probe or the write definitions. Writing goes through the writer only."""
    import ast
    from pathlib import Path

    from custom_components import weishaupt
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    await settled(hass, entry)
    assert entry.runtime_data.writer is None
    assert hass.services.async_services().get(DOMAIN) is None
    assert hass.states.async_entity_ids("number") == [] and hass.states.async_entity_ids("switch") == []
    assert [c for _, c in fake.commands if c.split()[0] not in ("info", "find", "read") or "-w" in c] == []
    package = Path(weishaupt.__file__).parent
    assert not (package / "services.yaml").exists()
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text())
        calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        if path.name != "writer.py":  # the only module that sends a write
            assert not calls & {"write_register", "probe_write"}, path.name
        assert path.stem not in ("button", "date", "time", "text", "climate", "water_heater"), path.name
