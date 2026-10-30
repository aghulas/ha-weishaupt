"""Frames checked against telegrams answered on the école Sainte-Marie bus (30/10/2026)."""
import pytest

from weishaupt_core.protocol import TEMP10, UNIT, EbusdError, crc_weishaupt, parse_read_answer, read_command, write_command


def test_crc_of_live_read():
    assert crc_weishaupt(bytes.fromhex("0500")) == 0x70


def test_read_command_matches_live_frames():
    assert read_command("35", ["0500"]) == "hex 35502203700500"
    assert read_command("35", ["1b01", "1c01", "1d01", "1e01"]) == "hex 35502209851b011c011d011e01"


def test_read_command_limits():
    with pytest.raises(ValueError):
        read_command("35", ["0500"] * 5)


def test_write_command_matches_accepted_writes():
    assert write_command("35", "0500", bytes.fromhex("d700"), "ff") == "hex -s ff 35502305d80500d700"
    assert write_command("35", "1b01", bytes.fromhex("1e00"), "ff") == "hex -s ff 35502305181b011e00"
    assert write_command("35", "1014", bytes.fromhex("491a")).startswith("hex 3550230")


def test_parse_read_answer():
    regs = ["1f01", "2001", "2d01", "3d01"]
    assert parse_read_answer("080b001a0000800000", regs) == {
        "1f01": b"\x0b\x00", "2001": b"\x1a\x00", "2d01": None, "3d01": b"\x00\x00"}
    with pytest.raises(EbusdError):
        parse_read_answer("0400000000", regs)


def test_codecs():
    assert TEMP10.decode(bytes.fromhex("d200")) == 21.0
    assert TEMP10.encode(74.5) == bytes.fromhex("e902")
    assert TEMP10.decode(bytes.fromhex("18fc")) == -100.0
    assert UNIT.encode(26) == bytes.fromhex("1a00")


def test_effective_bounds_follow_linked_settings():
    from weishaupt_core.registers import FS_SETTINGS, effective_bounds
    by_key = {s.key: s for s in FS_SETTINGS}
    raw = {"0500": bytes.fromhex("d200"), "0800": bytes.fromhex("8c00")}  # 21.0 / 14.0
    assert effective_bounds(by_key["room_reduced"], FS_SETTINGS, raw) == (10, 21.0)
    assert effective_bounds(by_key["room_normal"], FS_SETTINGS, raw) == (16, 35)
    raw["0800"] = bytes.fromhex("aa00")  # reduced 17.0
    assert effective_bounds(by_key["room_normal"], FS_SETTINGS, raw) == (17.0, 35)
    assert effective_bounds(by_key["supply_min"], FS_SETTINGS, {}) == (8, 82)


def test_time_program_slots():
    from weishaupt_core.protocol import decode_slot, encode_slot, format_slots, parse_slots
    from weishaupt_core.registers import PROGRAMS
    assert decode_slot(bytes.fromhex("481a")) == (390, 1080)  # 06:30-18:00, read on FS1
    assert decode_slot(bytes.fromhex("8080")) is None
    assert encode_slot((390, 1095)) == bytes.fromhex("491a")  # end 18:15, written and read back on FS1
    assert format_slots([(390, 1080), None, None]) == "06:30-18:00"
    assert parse_slots("06:30-18:00, 19:00-21:00") == [(390, 1080), (1140, 1260)]
    assert parse_slots("-") == []
    for bad in ("18:00-06:30", "06:10-18:00", "06:00-12:00, 11:00-13:00", "1:00-2:00,3:00-4:00,5:00-6:00,7:00-8:00"):
        with pytest.raises(ValueError):
            parse_slots(bad)
    heating_1 = PROGRAMS[0]
    assert heating_1.register(1, 1) == "1014" and heating_1.register(3, 1) == "3014" and heating_1.register(7, 3) == "7214"


def test_datetime_broadcast_matches_live_frame():
    from weishaupt_core.protocol import datetime_broadcast_command
    # broadcast sent at 17:59:00 on Friday (weekday 5) 30/10/2026, which reset the whole installation to the right time
    assert datetime_broadcast_command(0, 59, 17, 30, 10, 5, 26, bytes.fromhex("000d")) == \
        "hex fe070009000d00591730100526"


def test_datetime_broadcast_rejects_bad_input():
    from weishaupt_core.protocol import datetime_broadcast_command
    with pytest.raises(ValueError):
        datetime_broadcast_command(0, 0, 0, 1, 1, 8, 26, bytes.fromhex("000d"))  # weekday out of 1..7
    with pytest.raises(ValueError):
        datetime_broadcast_command(0, 0, 0, 1, 1, 1, 26, bytes.fromhex("00"))  # outside temp must be 2 bytes
    with pytest.raises(ValueError):
        datetime_broadcast_command(0, 0, 0, 1, 1, 1, 100, bytes.fromhex("000d"))  # year not BCD-representable


def test_parse_last_outside_raw():
    from weishaupt_core.protocol import parse_last_outside_raw
    grab = ("f1fe500a0d01000000ff34ff52000d4d0a0e = 2487: ka KaStatus\n"
            "f1fe070009000d04551830100526 = 419: sc InfoStatus\n")
    assert parse_last_outside_raw(grab) == bytes.fromhex("000d")
    assert parse_last_outside_raw("rien de pertinent") is None
