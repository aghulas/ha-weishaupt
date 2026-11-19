"""Weekly programs and the clock inside a Home Assistant test instance, against the simulated ebusd."""
from datetime import datetime, timedelta

import pytest
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr, entity_registry as er, issue_registry as ir
from homeassistant.util import dt as dt_util

from custom_components.weishaupt import clock
from custom_components.weishaupt.const import DOMAIN
from custom_components.weishaupt.guard import WriteRefused
from custom_components.weishaupt.writer import ConfirmationPending, WriteFailed
from ha_common import make_entry, settled, setup
from test_ha_writes import sent, switch_id, telegram_log


@pytest.fixture
def log(tmp_path):
    return telegram_log(tmp_path / "telegrams.db")


async def writing(hass, fake, log, **options):
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log, **options)
    await setup(hass, entry)
    await hass.services.async_call("switch", "turn_on", {"entity_id": switch_id(hass, entry)}, blocking=True)
    fake.commands.clear()
    return entry, entry.runtime_data.writer


def text_id(hass, entry, program: str, day: str) -> str | None:
    return er.async_get(hass).async_get_entity_id("text", DOMAIN, f"{entry.entry_id}_{program}/{day}")


def device_id(hass, entry, device: str) -> str:
    wanted = (DOMAIN, f"{entry.entry_id}_{device}")
    return next(d.id for d in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
                if wanted in d.identifiers)


async def test_program_entities(hass, fake, log):
    """One text per program and day where the definitions prove the slots: the 5 programs of room units 1 and 3,
    the hot-water and circulation programs of the system manager's own circuit (84 texts); nothing on room unit 2.
    Heating program 1 enabled when created (room units 1 and 3: 14), the others not."""
    entry, writer = await writing(hass, fake, log)
    registry = er.async_get(hass)
    texts = [e for e in er.async_entries_for_config_entry(registry, entry.entry_id) if e.domain == "text"]
    assert len(texts) == 12 * 7 == 84
    enabled = {e.unique_id.removeprefix(f"{entry.entry_id}_") for e in texts if not e.disabled_by}
    assert enabled == {f"{c}/heating1/{d}" for c in ("fs1", "fs3") for d in
                       ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")}
    assert not [e for e in texts if e.unique_id.removeprefix(f"{entry.entry_id}_").startswith("fs2/")]
    assert text_id(hass, entry, "em1/dhw", "monday") is not None
    await settled(hass, entry)
    monday = hass.states.get(text_id(hass, entry, "fs1/heating1", "monday"))
    assert monday.state == "06:30-18:00" and monday.attributes["pattern"]
    assert monday.attributes["friendly_name"].endswith("Heating program 1 – Monday (setting)")
    assert hass.states.get(text_id(hass, entry, "fs1/heating1", "sunday")).state == "-"


async def test_a_day_written_and_read_back(hass, fake, log):
    """Tuesday of heating program 1 of room unit 1, 06:30-22:30 -> 06:30-18:00, 19:00-21:00: slot 1 is the
    telegram captured on the bus (`52 20 14 48 1a` from 31), slot 2 the new range, slot 3 stays unused and is not
    written. Comfort: no confirmation."""
    entry, writer = await writing(hass, fake, log)
    await settled(hass, entry)
    fake.commands.clear()
    entity_id = text_id(hass, entry, "fs1/heating1", "tuesday")
    await hass.services.async_call("text", "set_value", {"entity_id": entity_id, "value": "06:30-18:00, 19:00-21:00"},
                                   blocking=True)
    slot2 = writer.slot_specs["fs1/HCProgram1Tue2"].telegram(0x4C54)
    assert fake.writes == [(None, "fs1", "3550230552201448" "1a"), (None, "fs1", slot2)]
    assert sent(fake) == ["write -c fs1 -h 35502305522014481a", f"write -c fs1 -h {slot2}"]
    assert hass.states.get(entity_id).state == "06:30-18:00, 19:00-21:00"
    assert not [i for i in ir.async_get(hass).issues.values() if i.domain == DOMAIN]


async def test_a_day_that_is_no_day_is_refused(hass, fake, log):
    entry, writer = await writing(hass, fake, log)
    with pytest.raises(WriteRefused) as err:
        await writer.async_write_day("fs1/heating1", 1, "06:20-18:00", None)
    assert err.value.code == "bad_day" and fake.writes == []


async def test_room_unit_2_is_refused(hass, fake, log):
    """Room unit 2 does not keep slot writes: the definitions give its programs no write conditions."""
    entry, writer = await writing(hass, fake, log)
    with pytest.raises(WriteRefused) as err:
        await writer.async_set_program("fs2/heating1", {1: "06:30-18:00"}, None)
    assert err.value.code == "not_writable"
    with pytest.raises(ServiceValidationError) as shown:
        await hass.services.async_call(DOMAIN, "set_program", {
            "device_id": device_id(hass, entry, "room2"), "program": "heating1", "monday": "06:30-18:00"},
            blocking=True)
    assert shown.value.translation_key == "not_writable" and fake.writes == []


async def test_set_program_for_a_week(hass, fake, log):
    """The action writes the slots that change and answers what it did: here 7 days, one range each, of which
    Monday is already so: 6 slot writes for 6 days (Tuesday's slot 1, and slot 1 of the five empty days)."""
    entry, writer = await writing(hass, fake, log)
    days = {day: "06:30-18:00" for day in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
                                            "sunday")}
    for key in ("fs1/HCProgram1Wed1", "fs1/HCProgram1Thu1", "fs1/HCProgram1Fri1", "fs1/HCProgram1Sat1"):
        fake.reads[key] = "00:00;Disabled;00:00;Disabled"
    result = await hass.services.async_call(DOMAIN, "set_program", {
        "device_id": device_id(hass, entry, "room1"), "program": "heating1", **days}, blocking=True,
        return_response=True)
    assert result["written"] == 6 and result["unchanged"] == 15
    assert len(fake.writes) == 6 and all(w[0] is None for w in fake.writes)  # from 31, as the metadata says
    assert writer.program_day(writer.programs["fs1/heating1"], 7) == "06:30-18:00"


async def test_set_program_within_the_hourly_limit(hass, fake, log):
    """More slots to write than writes left in the hour: nothing is written, the action says how many."""
    entry, writer = await writing(hass, fake, log, max_writes_per_hour=2)
    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(DOMAIN, "set_program", {
            "device_id": device_id(hass, entry, "room1"), "program": "heating1",
            "tuesday": "06:00-08:00, 10:00-12:00, 14:00-16:00"}, blocking=True)
    assert err.value.translation_key == "program_limit"
    assert err.value.translation_placeholders == {"needed": "3", "left": "2", "limit": "2"}
    assert fake.writes == []


async def test_set_program_without_writes(hass, fake):
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(DOMAIN, "set_program", {
            "device_id": device_id(hass, entry, "room1"), "program": "heating1", "monday": "-"}, blocking=True)
    assert err.value.translation_key == "writes_disabled"


# ---- the clock ----------------------------------------------------------------------------------------------


class Clock:
    """Home Assistant's time for the writer: `sleep` moves it on, by what is asked plus `overshoot`."""

    def __init__(self, start: datetime, overshoot: float = 0.0) -> None:
        self.now, self.overshoot, self.slept = start, overshoot, []

    def __call__(self) -> datetime:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += timedelta(seconds=seconds + self.overshoot)


def master_broadcast(carried: datetime) -> str:
    return "f1" + clock.telegram(carried, 12.0)


async def test_clock_offset_sensor(hass, fake, log):
    """From the last broadcast ebusd holds, without a bus request: 7 s behind."""
    now = dt_util.now().replace(microsecond=0, tzinfo=None)  # ebusd's host on Home Assistant's time zone
    fake.clock_raw, fake.clock_received = master_broadcast(now - timedelta(seconds=7)), now
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    sensor = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_broadcast/Datetime/offset")
    state = hass.states.get(sensor)
    assert state.state == "-7.0" and state.attributes["master"] == "f1"
    # from ebusd's cache: one `find`, no read request of the broadcast
    assert fake.reads_of("write") == [] and not [c for _, c in fake.reads_of() if "Datetime" in c]
    assert any(c == "find -p -h -vvv -c broadcast Datetime" for _, c in fake.commands)


async def test_clock_offset_unknown_when_ebusd_host_disagrees(hass, fake):
    now = dt_util.now().replace(microsecond=0, tzinfo=None)
    fake.clock_raw, fake.clock_received = master_broadcast(now), now - timedelta(hours=1)
    entry = make_entry(hass, fake)
    await setup(hass, entry)
    sensor = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_broadcast/Datetime/offset")
    assert hass.states.get(sensor).state == "unknown"


async def test_set_clock_at_second_00(hass, fake, log):
    """The button asks for a confirmation; confirmed at 11:44:59.5, the broadcast goes out at 11:45:00 exactly:
    the telegram of the evidence record (`fe 07 00` `00 0c 00 45 11 18 11 03 26`), from ebusd's own address."""
    from homeassistant.components.repairs import repairs_flow_manager
    from homeassistant.setup import async_setup_component
    entry, writer = await writing(hass, fake, log)
    tz = dt_util.get_default_time_zone()
    fake_clock = Clock(datetime(2026, 11, 18, 11, 44, 59, 500000, tzinfo=tz))
    writer._now, writer._sleep = fake_clock, fake_clock.sleep
    fake.clock_raw = master_broadcast(datetime(2026, 11, 18, 11, 44, 4))  # 12.0 °C outside, as the master sent
    button = er.async_get(hass).async_get_entity_id("button", DOMAIN, f"{entry.entry_id}_broadcast/Datetime/set")
    await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
    assert fake.writes == []
    issue = next(i for i in ir.async_get(hass).issues.values() if i.translation_key == "confirm_clock")
    assert issue.translation_placeholders["source"] == "31"
    assert await async_setup_component(hass, "repairs", {})
    manager = repairs_flow_manager(hass)
    result = await manager.async_init(DOMAIN, data={"issue_id": issue.issue_id})
    assert result["step_id"] == "confirm"
    result = await manager.async_configure(result["flow_id"], {})
    assert result["type"] == "create_entry" and result["description"] == "sent"
    assert result["description_placeholders"]["sent"] == "11:45:00"
    assert result["description_placeholders"]["telegram"] == "31fe070009000c00451118110326"
    assert fake.writes == [(None, "Broadcast", "fe070009000c00451118110326")]
    assert sent(fake) == ["write -c Broadcast -h fe070009000c00451118110326"]
    assert fake_clock.now == datetime(2026, 11, 18, 11, 45, 0, tzinfo=tz)  # sent at second 00, not before


async def test_set_clock_gives_up_rather_than_send_late(hass, fake, log):
    """The connection is not free within 2 s of second 00 (here the wait overran by 2.5 s): nothing is sent."""
    entry, writer = await writing(hass, fake, log)
    tz = dt_util.get_default_time_zone()
    fake_clock = Clock(datetime(2026, 11, 18, 11, 44, 59, tzinfo=tz), overshoot=2.5)
    writer._now, writer._sleep = fake_clock, fake_clock.sleep
    with pytest.raises(WriteFailed) as err:
        await writer.async_set_clock(None)
    assert err.value.code == "clock_late" and fake.writes == [] and sent(fake) == []
    assert writer.journal[-1]["result"] == "given up"


async def test_set_clock_needs_its_confirmation_and_the_switch(hass, fake, log):
    entry, writer = await writing(hass, fake, log)
    with pytest.raises(ConfirmationPending):
        await writer.async_request_clock(None)
    writer.set_switch(False)
    with pytest.raises(WriteRefused) as err:
        await writer.async_request_clock(None)
    assert err.value.code == "writes_disabled" and fake.writes == []


async def test_the_hot_water_program_of_the_manager(hass, fake, log):
    """The hot-water program the installation applies (em1, address 50): comfort in the metadata, so written
    without a confirmation, from ebusd's own address, read back; no looser than that class."""
    entry, writer = await writing(hass, fake, log)
    spec = writer.slot_specs["em1/DHWProgramMon1"]
    assert (spec.risk, spec.source, spec.zz) == ("comfort", "31", "50")
    fake.reads["em1/DHWProgramMon1"] = "00:00;Disabled;00:00;Disabled"
    result = await writer.async_write_day("em1/dhw", 1, "06:00-07:00", None)
    assert result["written"] == 1 and fake.writes == [(None, "em1", spec.telegram(0x181C))]
    assert writer.program_day(writer.programs["em1/dhw"], 1) == "06:00-07:00"
    assert not [i for i in ir.async_get(hass).issues.values() if i.domain == DOMAIN]


async def test_enabled_program_days_are_read_right_after_the_settings(hass, fake, log):
    """Every entity enabled, as on an installation where diagnostics and programs are shown, but the program texts
    as created (heating program 1 only): after a start, the 42 slots of the 14 enabled texts are read right after
    the live values and the numbers and selects, not after the whole first pass. A text stays unknown until its
    three slots are read. Measured as a count of bus requests; at the installation's pace (about 0.4 requests a
    second) it gives the time to values."""
    from unittest.mock import patch
    from homeassistant.helpers.entity import Entity
    from custom_components.weishaupt.text import ProgramDayText

    def enabled_default(self):  # everything enabled, except the program texts that are not enabled by default
        return self._attr_entity_registry_enabled_default if isinstance(self, ProgramDayText) else True

    with patch.object(Entity, "entity_registry_enabled_default", property(enabled_default)):
        entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log)
        await setup(hass, entry)
    hub = entry.runtime_data
    registry = er.async_get(hass)
    texts = [registry.async_get_entity_id("text", DOMAIN, f"{entry.entry_id}_{c}/heating1/{d}")
             for c in ("fs1", "fs3") for d in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
                                               "sunday")]
    assert len(texts) == 14
    # unknown until the three slots are read
    assert all(hass.states.get(t).state == "unknown" for t in texts)
    from ha_common import wait_until
    await wait_until(lambda: all(hass.states.get(t).state not in ("unknown", "unavailable") for t in texts))
    bus = [c for _, c in fake.reads_of() if not hub.model.messages[c.split()[-2] + "/" + c.split()[-1]].passive]
    listened = len(hub.listened())
    requests_until_texts = len(bus)
    await settled(hass, entry)
    total = len([c for _, c in fake.reads_of()
                 if not hub.model.messages[c.split()[-2] + "/" + c.split()[-1]].passive])
    # settings and program days first: the texts have their values after about a third of the first pass
    assert requests_until_texts < total / 2, (requests_until_texts, total)
    print(f"\nmessages listened {listened}, bus requests of the first pass {total}, "
          f"until the 14 texts have values {requests_until_texts} "
          f"(~{requests_until_texts / 0.4 / 60:.0f} min at 0.4 requests/s, against ~{total / 0.4 / 60:.0f} min)")
