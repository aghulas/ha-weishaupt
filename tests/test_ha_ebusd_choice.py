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
