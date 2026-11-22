"""Weekly programs and the clock, without Home Assistant: the text of a day, the bytes of a slot and of the date and
time broadcast, against the captures of the definitions release and the answers of a real ebusd."""
import json
from datetime import datetime

import pytest

from conftest import DATA
from weishaupt_core.clock import offset, parse_find, telegram, next_minute
from weishaupt_core.ebusd import parse_definitions
from weishaupt_core.model import Model
from weishaupt_core.programs import (
    UNUSED,
    DayError,
    format_day,
    parse_day,
    program_specs,
    range_of_raw,
    raw_of_fields,
    raws_of_day,
)


@pytest.fixture(scope="module")
def model():
    return Model.load()


@pytest.fixture(scope="module")
def programs(model, golden):
    loaded = {circuit: parse_definitions(text) for circuit, text in golden["write_definitions"].items()}
    return program_specs(model, loaded)


@pytest.mark.parametrize("text,ranges", [
    ("06:30-18:00", [(26, 72)]),
    ("06:30-18:00, 19:00-21:00", [(26, 72), (76, 84)]),
    ("19:00-21:00,06:30-18:00", [(26, 72), (76, 84)]),  # sorted
    ("00:00-06:00, 12:00-13:15, 22:00-24:00", [(0, 24), (48, 53), (88, 96)]),
    ("-", []), ("", []),
])
def test_parse_and_format_round_trip(text, ranges):
    assert parse_day(text) == ranges
    assert parse_day(format_day(ranges)) == ranges
    assert format_day(ranges) == (", ".join(sorted(p.strip() for p in text.split(","))) if ranges else "-")


@pytest.mark.parametrize("text", [
    "06:20-18:00", "18:00-06:30", "06:30-06:30", "06:30-18:00, 17:00-19:00", "1-2, 3-4",
    "00:00-01:00, 02:00-03:00, 04:00-05:00, 06:00-07:00", "06:30-24:15", "6h30-18h"])
def test_what_is_not_a_day(text):
    with pytest.raises(DayError):
        parse_day(text)


def test_slots_of_a_day():
    """`48 1a` is 06:30-18:00 (end low byte, start high byte), an unused slot `80 80`."""
    assert raws_of_day(parse_day("06:30-18:00")) == [0x1A48, UNUSED, UNUSED]
    assert range_of_raw(0x1A48) == (26, 72) and range_of_raw(UNUSED) is None
    assert range_of_raw(0x9A48) is None  # start disabled: not a range
    assert raw_of_fields(("18:00", "Enabled", "06:30", "Enabled")) == 0x1A48
    assert raw_of_fields(("00:00", "Disabled", "00:00", "Disabled")) == UNUSED
    assert raw_of_fields(("18:00", "Enabled")) is None


def test_the_programs_the_definitions_prove(programs):
    """The five programs of room units 1 and 3, the hot-water and circulation programs of the system manager's own
    circuit (em1, the hot-water program the installation applies); nothing of room unit 2, whose program 1 is kept
    by room unit 1 and changed there. 252 slots."""
    found, specs, refused = programs
    assert sorted(found) == [f"{c}/{p}" for c in ("em1",) for p in ("circulation", "dhw")] + [
        f"{c}/{p}" for c in ("fs1", "fs3") for p in ("circulation_stored", "dhw_stored", "heating1", "heating2",
                                                     "heating3")]
    assert refused == [
        "fs2/heating1: kept by fs1/heating1, changed there",
        "fs2/heating2: kept by fs1/heating2, changed there",
        "fs2/heating3: kept by fs1/heating3, changed there",
        "fs2/dhw_stored: kept by fs1/dhw_stored, changed there",
        "fs2/circulation_stored: kept by fs1/circulation_stored, changed there",
    ] and len(specs) == 12 * 21 == 252
    assert not [key for key in specs if key.startswith("fs2/")]
    assert found["fs1/heating1"].day_keys(7) == ("fs1/HCProgram1Sun1", "fs1/HCProgram1Sun2", "fs1/HCProgram1Sun3")
    sun3 = specs["fs1/HCProgram1Sun3"]
    assert (sun3.register, sun3.source, sun3.risk, sun3.zz) == ("7214", "31", "comfort", "35")
    dhw = specs["em1/DHWProgramMon1"] if "em1/DHWProgramMon1" in specs else None
    assert dhw is not None and (dhw.risk, dhw.source, dhw.zz) == ("comfort", "31", "50")


def test_a_program_of_another_class_is_not_offered(model, golden):
    """Every day is written without a confirmation: a program whose slots the metadata classes otherwise is left
    read-only, rather than written more loosely than its class."""
    import dataclasses
    loaded = {circuit: parse_definitions(text) for circuit, text in golden["write_definitions"].items()}
    key = "em1/DHWProgramMon1"
    message = model.messages[key]
    changed = dataclasses.replace(message, write=dataclasses.replace(message.write, risk="regulation"))
    found, _, refused = program_specs(dataclasses.replace(model, messages=model.messages | {key: changed}), loaded)
    assert "em1/dhw" not in found and refused and refused[0].startswith("em1/dhw")


def test_every_captured_slot_write_is_built_byte_for_byte(programs):
    """The slot telegrams captured on the bus (room units 1 and 3), from the fields the capture decodes to."""
    _, specs, _ = programs
    captured = [r for r in json.loads((DATA / "fixtures.json").read_text())["readings"]
                if r["type"] == "write" and "Program" in r["message"]]
    assert len(captured) >= 12
    for reading in captured:
        key = f"{reading['circuit']}/{reading['message']}"
        d = reading["decoded"]
        raw = raw_of_fields((d["totime"], d["toenabled"], d["fromtime"], d["fromenabled"]))
        expected = f"{reading['zz']}5023{len(reading['master'].split()):02x}{reading['master'].replace(' ', '')}"
        assert specs[key].telegram(raw) == expected, key
        assert reading["qq"] == specs[key].source


def test_a_week_is_21_slots_at_most():
    week = {day: raws_of_day(parse_day("06:30-18:00, 19:00-21:00")) for day in range(1, 8)}
    assert sum(len(raws) for raws in week.values()) == 21


def test_the_clock_broadcast_of_the_evidence():
    """`31 fe 0700` `00 0c 00 45 11 18 11 03 26`: 12.0 °C, 11:45:00, Wednesday 18 November 2026."""
    assert telegram(datetime(2026, 11, 18, 11, 45, 0), 12.0) == "fe070009000c00451118110326"
    assert next_minute(datetime(2026, 11, 18, 11, 44, 59, 500000)) == datetime(2026, 11, 18, 11, 45)
    assert next_minute(datetime(2026, 11, 18, 11, 45, 0)) == datetime(2026, 11, 18, 11, 46)


def test_the_last_broadcast_as_ebusd_gives_it(golden):
    broadcast = parse_find(golden["clock"]["answer"])
    assert (broadcast.source, broadcast.carried, broadcast.outside) == (
        "f1", datetime(2026, 11, 18, 14, 47, 5), 13.0)
    assert parse_find("Broadcast Datetime = no data stored [ZZ=fe, passive read]") is None
    received = broadcast.received
    assert offset(broadcast, "31", received) == (broadcast.carried - received).total_seconds()
    assert offset(broadcast, "f1", received) is None  # sent by ebusd itself
    stale = received.replace(hour=(received.hour + 1) % 24)
    assert offset(broadcast, "31", stale) is None  # another clock or time zone, or old
