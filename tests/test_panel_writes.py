"""Writes from the panel: the same writer, guard and read-back as the entities; a regulation change and the clock
are confirmed in the panel's own dialog instead of a repair. Admin only."""
from __future__ import annotations

from datetime import datetime

from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util

from ha_common import make_entry, settled, setup
from test_ha_programs import Clock, log, master_broadcast, writing  # noqa: F401  (log is a fixture)
from test_ha_writes import sent


async def _ask(client, **message):
    _ask.next = getattr(_ask, "next", 0) + 1
    await client.send_json({"id": _ask.next, **message})
    return await client.receive_json()


async def test_comfort_setting_written_from_the_panel(hass, fake, log, hass_ws_client):
    entry, writer = await writing(hass, fake, log)
    client = await hass_ws_client(hass)
    answer = await _ask(client, type="weishaupt/panel/write", entry_id=entry.entry_id, key="em2/RoomNormalTemp",
                        value=22)
    result = answer["result"]
    assert result["status"] == "written" and result["result"] == "ok"
    assert (result["before"], result["after"], result["read_back"]) == ("21.5 °C", "22.0 °C", "22.0 °C")
    assert result["frame"] == "ff51502305640500dc00" and result["result_text"] == "read back ok"
    assert result["guard"]["writes_last_hour"] == 1
    assert fake.writes == [("ff", "em2", "51502305640500dc00")]  # the entity's telegram, through the same writer


async def test_regulation_setting_confirmed_in_the_panel(hass, fake, log, hass_ws_client):
    """ka blocking time 1 -> 2: `confirm` with the facts of the repair, no repair and nothing written; confirmed:
    the telegram of the write test, read back."""
    entry, writer = await writing(hass, fake, log)
    await settled(hass, entry)
    fake.commands.clear()
    client = await hass_ws_client(hass)
    answer = (await _ask(client, type="weishaupt/panel/write", entry_id=entry.entry_id, key="ka/BlockingTime",
                         value=2))["result"]
    assert answer["status"] == "confirm" and answer["kind"] == "setting"
    shown = answer["placeholders"]
    assert (shown["current"], shown["requested"], shown["address"], shown["register"], shown["source"]) == (
        "1 min", "2 min", "15", "25 00", "ff")
    assert fake.writes == [] and sent(fake) == []
    assert not [i for i in ir.async_get(hass).issues.values() if i.translation_key == "confirm_write"]
    result = (await _ask(client, type="weishaupt/panel/confirm", entry_id=entry.entry_id,
                         pending_id=answer["pending_id"]))["result"]
    assert result["status"] == "written" and result["frame"] == "ff15502305cc25000200"
    assert result["read_back"] == "2 min"
    # confirmed once: a second confirmation has nothing left to write
    again = (await _ask(client, type="weishaupt/panel/confirm", entry_id=entry.entry_id,
                        pending_id=answer["pending_id"]))["result"]
    assert again["status"] == "refused" and again["code"] == "expired"
    assert len(fake.writes) == 1


async def test_a_withdrawn_change_writes_nothing(hass, fake, log, hass_ws_client):
    entry, writer = await writing(hass, fake, log)
    client = await hass_ws_client(hass)
    answer = (await _ask(client, type="weishaupt/panel/write", entry_id=entry.entry_id, key="ka/BlockingTime",
                         value=2))["result"]
    cancel = (await _ask(client, type="weishaupt/panel/cancel", entry_id=entry.entry_id,
                         pending_id=answer["pending_id"]))["result"]
    assert cancel == {"withdrawn": True} and writer.pending == {}
    late = (await _ask(client, type="weishaupt/panel/confirm", entry_id=entry.entry_id,
                       pending_id=answer["pending_id"]))["result"]
    assert late["status"] == "refused" and late["code"] == "expired" and fake.writes == []


async def test_the_guard_refuses_from_the_panel_as_from_an_entity(hass, fake, log, hass_ws_client):
    """Switch off, out of range, off step, a setting not proven on that device, the hourly limit: refused by the
    writer's guard, with the entity's translated message; nothing sent."""
    entry = make_entry(hass, fake, writes_enabled=True, telegram_db=log, max_writes_per_hour=1)
    await setup(hass, entry)
    writer = entry.runtime_data.writer
    client = await hass_ws_client(hass)

    async def write(key, value, language="en"):
        return (await _ask(client, type="weishaupt/panel/write", entry_id=entry.entry_id, key=key, value=value,
                           language=language))["result"]

    off = await write("em2/RoomNormalTemp", 22)
    assert off["status"] == "refused" and off["code"] == "writes_disabled" and off["message"]
    writer.set_switch(True)
    assert (await write("em2/RoomNormalTemp", 99))["code"] == "out_of_bounds"
    assert (await write("em2/RoomNormalTemp", 21.3))["code"] == "off_step"
    unproven = await write("bc1/SupplyTemp", 21)  # a message without write conditions
    assert unproven["code"] == "not_writable"
    french = await write("em2/RoomNormalTemp", 99, "fr")
    assert french["code"] == "out_of_bounds" and french["message"] != off["message"]
    assert (await write("em2/RoomSetbackTemp", 21.0))["status"] == "written"
    limited = await write("em2/RoomNormalTemp", 22)
    assert limited["code"] == "hourly_limit" and len(fake.writes) == 1


async def test_program_days_written_from_the_panel(hass, fake, log, hass_ws_client):
    entry, writer = await writing(hass, fake, log)
    client = await hass_ws_client(hass)
    result = (await _ask(client, type="weishaupt/panel/write_days", entry_id=entry.entry_id,
                         program="fs1/heating1", days={"7": "02:00-02:15", "6": "02:00-02:15"}))["result"]
    assert result["status"] == "written" and result["written"] == 2
    assert result["days"]["7"]["after"] == "02:00-02:15" and result["days"]["7"]["result_text"] == "read back ok"
    assert len(fake.writes) == 2 and result["guard"]["writes_last_hour"] == 2
    bad = (await _ask(client, type="weishaupt/panel/write_days", entry_id=entry.entry_id, program="fs1/heating1",
                      days={"1": "2h-3h"}))["result"]
    assert bad["status"] == "refused" and bad["code"] == "bad_day_format" and "06:30-18:00" in bad["message"]
    unproven = (await _ask(client, type="weishaupt/panel/write_days", entry_id=entry.entry_id,
                           program="fs2/heating1", days={"1": "06:00-07:00"}))["result"]
    assert unproven["status"] == "refused"
    assert len(fake.writes) == 2


async def test_clock_set_from_the_panel_after_its_confirmation(hass, fake, log, hass_ws_client):
    entry, writer = await writing(hass, fake, log)
    tz = dt_util.get_default_time_zone()
    fake_clock = Clock(datetime(2026, 11, 18, 11, 44, 59, 500000, tzinfo=tz))
    writer._now, writer._sleep = fake_clock, fake_clock.sleep
    fake.clock_raw = master_broadcast(datetime(2026, 11, 18, 11, 44, 4))
    client = await hass_ws_client(hass)
    answer = (await _ask(client, type="weishaupt/panel/clock", entry_id=entry.entry_id))["result"]
    assert answer["status"] == "confirm" and answer["kind"] == "clock"
    assert answer["placeholders"]["send_at"] == "11:45:00" and answer["placeholders"]["source"] == "31"
    assert fake.writes == [] and not [i for i in ir.async_get(hass).issues.values()
                                      if i.translation_key == "confirm_clock"]
    result = (await _ask(client, type="weishaupt/panel/confirm", entry_id=entry.entry_id,
                         pending_id=answer["pending_id"]))["result"]
    assert result["status"] == "written" and result["result"] == "sent" and result["result_text"] == "sent"
    assert result["frame"] == "31fe070009000c00451118110326"
    assert fake.writes == [(None, "Broadcast", "fe070009000c00451118110326")]


async def test_writes_are_for_administrators_and_need_writes_enabled(hass, fake, log, hass_ws_client,
                                                                      hass_read_only_access_token):
    entry, writer = await writing(hass, fake, log)
    reader = await hass_ws_client(hass, hass_read_only_access_token)
    for message in ({"type": "weishaupt/panel/write", "key": "em2/RoomNormalTemp", "value": 22},
                    {"type": "weishaupt/panel/write_days", "program": "fs1/heating1", "days": {"1": "-"}},
                    {"type": "weishaupt/panel/clock"}):
        answer = await _ask(reader, entry_id=entry.entry_id, **message)
        assert not answer["success"] and answer["error"]["code"] == "unauthorized"
    assert fake.writes == []
    plain = make_entry(hass, fake)
    await setup(hass, plain)
    admin = await hass_ws_client(hass)
    answer = await _ask(admin, type="weishaupt/panel/write", entry_id=plain.entry_id, key="em2/RoomNormalTemp",
                        value=22)
    assert not answer["success"] and answer["error"]["code"] == "writes_disabled"
