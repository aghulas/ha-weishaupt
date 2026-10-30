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
