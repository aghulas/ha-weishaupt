"""The first pass after a start, timed with a simulated ebusd that answers like the one of the installation: its
own cache (ebusd stays up while Home Assistant restarts, and answers a read younger than `-m` seconds at once,
without a telegram) and the answer times measured there in phase 1 (median 0.18 s from the bus, under 0.05 s
from the cache). Time runs 100 times faster than on the installation; the figures printed are scaled back.

Everything is enabled as on the installation (entities enabled by default, the settings, the program texts of
heating program 1), with writes enabled, and ebusd's cache holds a fresh value of every message, as after a
restart of Home Assistant alone."""
import time

import pytest
from homeassistant.helpers.entity import Entity

from custom_components.weishaupt import hub as hub_module
from ha_common import make_entry, setup, wait_until
from test_ha_writes import telegram_log

K = 0.01  # simulated seconds per second of the installation
GAP, CYCLIC, BUS, CACHE = 2.0, 300, 0.18, 0.02


def key_of(command: str) -> str:
    return command.split()[-2] + "/" + command.split()[-1]


async def first_pass(hass, fake, tmp_path, monkeypatch, fixed: bool) -> dict:
    monkeypatch.setattr(hub_module, "REPEAT_DURING_FIRST_PASS", 900 * K if fixed else 0)
    monkeypatch.setattr(hub_module, "FIRST_READ_FROM_DEVICE", fixed)
    fake.model_cache, fake.latency_bus, fake.latency_cache = True, BUS * K, CACHE * K
    now = time.monotonic()
    fake.cache = {key: now for key in fake.reads}  # ebusd stayed up: it holds a fresh value of everything
    entry = make_entry(hass, fake, gap=GAP * K, cyclic_interval=CYCLIC * K, writes_enabled=True,
                       telegram_db=telegram_log(tmp_path / "t.db"))
    start = time.monotonic()
    await setup(hass, entry)
    hub, writer = entry.runtime_data, entry.runtime_data.writer
    settings = {d.message.key for d in hub.model.setting_entities if d.message.key in writer.specs}
    slots = {k for p in ("fs1/heating1", "fs3/heating1") for day in writer.programs[p].slots.values() for k in day}
    deadline = 3600 * K
    await wait_until(lambda: hub.first_pass_done is not None or time.monotonic() - start > deadline,
                     timeout=deadline + 5)

    def when(keys: set[str]) -> float | None:
        seen = [t for t, k in fake.bus if k in keys]
        return (max(seen) - start) / K if {k for _, k in fake.bus} >= keys else None

    asked = [key_of(c) for _, c in fake.reads_of() if not hub.model.messages[key_of(c)].passive]
    cyclic = {k for k in hub.listened() if hub.model.messages[k].poll == "cyclic"}
    return {"settings": when(settings), "slots": when(slots),
            "pass": (hub.first_pass_done - (time.time() - (time.monotonic() - start))) / K
            if hub.first_pass_done else None,
            "requests": len(asked), "bus": len(fake.bus), "listened": len(hub.listened()),
            "cyclic_repeats": len(asked) - len(set(asked)), "cyclic": len(cyclic)}


@pytest.fixture
def as_installation():
    from unittest.mock import patch
    from custom_components.weishaupt.text import ProgramDayText

    def enabled_default(self):
        return self._attr_entity_registry_enabled_default if isinstance(self, ProgramDayText) else True

    with patch.object(Entity, "entity_registry_enabled_default", property(enabled_default)):
        yield


async def test_first_pass_as_before_the_fix(hass, fake, tmp_path, monkeypatch, as_installation):
    """The behaviour of 0.3.0rc5 reproduced: ebusd answers the first pass from its cache, so the slots and most
    settings never reach the bus, and the live values come back every 5 minutes ahead of the pass."""
    result = await first_pass(hass, fake, tmp_path, monkeypatch, fixed=False)
    print(f"\nrc5: {result}")
    assert result["slots"] is None  # none of the 42 slots read from the bus
    assert result["bus"] < result["requests"] * 0.55


async def test_first_pass_reads_everything_from_the_device(hass, fake, tmp_path, monkeypatch, as_installation):
    """rc6: every enabled message is asked from the device once, settings and the 42 slots right after the live
    values, and the pass ends."""
    result = await first_pass(hass, fake, tmp_path, monkeypatch, fixed=True)
    print(f"\nrc6: {result}")
    assert result["settings"] is not None and result["slots"] is not None and result["pass"] is not None
    assert result["settings"] < result["slots"] < result["pass"]
    assert result["slots"] < 0.4 * result["pass"]
    assert result["bus"] >= result["listened"] - 20  # every enabled message but the passive ones went to the bus
