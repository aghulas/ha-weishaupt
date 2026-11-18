"""0.1.1: numeric settings written as raw 5023 frames, byte-identical to the named writes of 0.1.0 (0.1.3: except the
source byte of the em1 flow limits, sent from ff, see SOURCE_CHANGED_0_1_3).

Three sources of expected bytes, each test says which one it uses:
- captured: `50 23` telegrams seen on the bus of the test installation (2026-11-16/17), acknowledged by the device;
- ebusd: what the library of the ebusd fork builds from the write definition 0.1.0 used, `data/named-write-telegrams.csv`;
- definition: the encoding rule of the definition line itself (type, divisor), `data/named-write-definitions.csv`,
  checked for every value of the setting's range.
"""
import csv
from pathlib import Path

import pytest

from weishaupt_core.guard import WriteGuard, WriteRefused
from weishaupt_core.protocol import crc_weishaupt, write_command
from weishaupt_core.registers import DEVICES, NAMED_WRITES, effective_bounds, settings_of

DATA = Path(__file__).resolve().parent / "data"
DEVICE = {d.key: d for d in DEVICES}

# The message name 0.1.0 used for each setting key (identical on the room units and the modules).
MESSAGE_0_1_0 = {
    "ka": {"supply_max": "SupplyMaxTemp", "modulation_max": "ModulationMax", "modulation_min": "ModulationMin",
           "dhw_setpoint": "DHWSetpoint", "regulation_p": "RegulationP", "regulation_i": "RegulationI",
           "legionella_setup_temp": "LegionellaSetupTemp", "dhw_load_time": "DHWLoadTime",
           "dhw_switch_diff": "DHWSwitchDiff", "legionella_circ_time": "LegionellaCirculationTime",
           "cascade_change_time": "ChangeOverTime", "cascade_blocking_time": "BlockingTime",
           "decouple_min": "DeCoupleMin", "calorifier_switch_diff": "CalorfierSwitchDifference"},
    "fs": {"room_normal": "RoomNormalTemp", "room_reduced": "RoomSetbackTemp",
           "room_frost": "RoomFrostProtectionTemp", "gradient": "GradientCurve",
           "summer_winter": "SummerWinterChangeOverTemp", "supply_max": "SupplyMaxTemp",
           "supply_min": "SupplyMinTemp", "dhw_setpoint": "DHWSetpoint", "room_factor_curve": "RoomFactorCurve",
           "boiler_mc_boost": "BoilerMCBoostTemp", "switch_on_runtime": "SwitchOnRuntime",
           "frost_protection_limit": "FrostProtectionLimitTemp"},
}
MESSAGE_0_1_0["em"] = {k: v for k, v in MESSAGE_0_1_0["fs"].items()
                       if k in ("room_normal", "room_reduced", "room_frost", "gradient", "summer_winter",
                                "supply_max", "supply_min")}


def all_settings():
    return [(device, setting) for device in DEVICES for setting in settings_of(device)]


def message_of(device, setting):
    return MESSAGE_0_1_0[device.kind][setting.key]


def master(device, setting, value):
    """Master part of the raw telegram (source, target, 5023, length, data), as ebusd logs it."""
    command = write_command(device.zz, setting.register, setting.codec.encode(value), setting.source)
    return (setting.source or "31") + command.split()[-1]


def definitions():
    rows = {}
    for line in (DATA / "named-write-definitions.csv").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            p = line.split(",")
            rows[(p[1], p[2])] = p
    return rows


def grid(setting):
    n = round((setting.maximum - setting.minimum) / setting.step)
    return [setting.minimum + i * setting.step for i in range(n + 1)]


def test_71_settings_66_raw_5_named():
    pairs = all_settings()
    assert len(pairs) == 71
    named = [(d.key, s.key) for d, s in pairs if s.message]
    assert sorted(named) == sorted([("ka", "modulation_max"), ("ka", "modulation_min"), ("fs1", "room_factor_curve"),
                                    ("fs2", "room_factor_curve"), ("fs3", "room_factor_curve")])
    assert all(s.message in NAMED_WRITES and s.message == message_of(d, s) for d, s in pairs if s.message)


# --- captured -------------------------------------------------------------------------------------------------
# evidence/register-write-crc.md (section 1 and the write test of section 6) and evidence/settings-writes.md of the
# weishaupt-ebus workbench: master data of 50 23 telegrams seen on the bus, acknowledged with 00.
CAPTURED = [
    ("ka", "cascade_blocking_time", 1, "ff15502305" "2825000100"),
    ("ka", "cascade_blocking_time", 2, "ff15502305" "cc25000200"),
    ("ka", "cascade_change_time", 50, "ff15502305" "d4ecfd3200"),
    ("ka", "decouple_min", 8.0, "ff15502305" "70e7fd5000"),
    ("ka", "calorifier_switch_diff", 2.0, "ff15502305" "0ce2fd1400"),
    ("ka", "dhw_switch_diff", -5.0, "ff15502305" "bf4001ceff"),
    ("ka", "dhw_load_time", 0, "ff15502305" "9080010000"),
    ("ka", "legionella_setup_temp", 60.0, "ff15502305" "7287055802"),
    ("ka", "legionella_circ_time", 600, "ff15502305" "46b1095802"),
    ("ka", "regulation_p", 100, "ff15502305" "989f026400"),
    ("ka", "regulation_i", 100, "ff15502305" "909e026400"),
    ("fs1", "switch_on_runtime", 3, "ff35502305" "d810010300"),
    ("fs1", "boiler_mc_boost", 2.0, "ff35502305" "a811011400"),
    ("fs1", "frost_protection_limit", 0.0, "ff35502305" "a4be020000"),
    ("em2", "room_normal", 21.5, "ff51502305" "d80500d700"),
    ("em2", "room_reduced", 21.5, "ff51502305" "b00800d700"),
    ("em2", "room_frost", 10.0, "ff51502305" "7c140a6400"),
    ("em2", "gradient", 10.0, "ff51502305" "a40e016400"),
    ("em2", "summer_winter", 20.0, "ff51502305" "dc1601c800"),
    ("em2", "supply_max", 75.0, "3151502305" "662800ee02"),
    ("em2", "supply_min", 8.0, "3151502305" "702b015000"),
]


@pytest.mark.parametrize("device_key, key, value, expected", CAPTURED)
def test_raw_frame_equals_captured_telegram(device_key, key, value, expected):
    device = DEVICE[device_key]
    setting = next(s for s in settings_of(device) if s.key == key)
    assert setting.message is None
    assert master(device, setting, value) == expected


# 0.1.3: em1 (the system manager's direct circuit) ignores its flow limits written from 31 and takes them from ff.
# The CRC covers the register and value only, so the frame differs from the 0.1.0 named write by the source byte.
SOURCE_CHANGED_0_1_3 = {("em1", "supply_max"), ("em1", "supply_min")}


# --- ebusd ----------------------------------------------------------------------------------------------------
def ebusd_vectors():
    with (DATA / "named-write-telegrams.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


def test_ebusd_vectors_cover_every_setting():
    seen = {(row["device"], row["message"]) for row in ebusd_vectors()}
    assert seen == {(d.key, message_of(d, s)) for d, s in all_settings()}


@pytest.mark.parametrize("row", ebusd_vectors(), ids=lambda r: f"{r['device']}-{r['message']}-{r['value']}")
def test_raw_frame_equals_ebusd_named_write(row):
    device = DEVICE[row["device"]]
    setting = next(s for s in settings_of(device) if message_of(device, s) == row["message"])
    if setting.message:  # left on the named path: ebusd refuses every number for these definitions
        assert row["master"].startswith("ERR")
        return
    expected = row["master"]
    if (device.key, setting.key) in SOURCE_CHANGED_0_1_3:  # same frame, sent from ff instead of 31 (source byte only)
        assert expected.startswith("31") and setting.source == "ff"
        expected = "ff" + expected[2:]
    assert master(device, setting, float(row["value"])) == expected


# --- definition -----------------------------------------------------------------------------------------------
def encode_like_the_definition(row, value):
    """The data bytes of a definition `w,<circuit>,<name>,<comment>,,<zz>,5023,00<addr><sub>,<field>,m,<type>,<div>`:
    the value text (`%g`) times the divisor, rounded half away from zero, 16 bits little endian."""
    kind, divisor = row[10], row[11]
    factor = int(divisor) if divisor.isdigit() else 1
    scaled = float(f"{value:g}") * factor
    number = int(abs(scaled) + 0.5) * (1 if scaled >= 0 else -1)
    return number.to_bytes(2, "little", signed=(kind == "SIN"))


@pytest.mark.parametrize("device, setting", [p for p in all_settings() if not p[1].message],
                         ids=lambda x: getattr(x, "key", ""))
def test_raw_frame_follows_the_definition_over_the_whole_range(device, setting):
    row = definitions()[(device.key, message_of(device, setting))]
    assert row[0] == "w" and "[WCRC]" in row[3] and row[6] == "5023"
    assert row[5] == device.zz and row[7] == "00" + setting.register  # target, placeholder checksum, register
    assert row[10] in ("SIN", "UIN") and row[11] in ("", "10")  # a number: no value list, no range
    for value in grid(setting):
        data = bytes.fromhex(setting.register) + encode_like_the_definition(row, value)
        expected = (setting.source or "31") + device.zz + "502305" + f"{crc_weishaupt(data):02x}" + data.hex()
        assert master(device, setting, value) == expected, value


@pytest.mark.parametrize("message", sorted(NAMED_WRITES))
def test_named_writes_left_are_value_lists(message):
    rows = [row for (circuit, name), row in definitions().items() if name == message]
    assert rows and all(row[11] == "32768=Na" for row in rows)


# --- guard: the bounds are the only range check now -----------------------------------------------------------
# The definitions of the older configuration carry no range (see the test above); the release has one for 14 of
# these settings (evidence/settings-writes.md). The integration's own bounds must be inside every one of them.
RELEASE_RANGES = {
    ("ka", "cascade_blocking_time"): (0, 30), ("ka", "cascade_change_time"): (0, 250),
    ("ka", "decouple_min"): (0, 50), ("ka", "calorifier_switch_diff"): (1, 20), ("ka", "dhw_switch_diff"): (-10, -1),
    ("ka", "dhw_load_time"): (0, 180), ("ka", "legionella_setup_temp"): (40, 80),
    ("ka", "legionella_circ_time"): (180, 1200),
    ("em2", "room_normal"): (16, 35), ("em2", "room_frost"): (4, 16), ("em2", "summer_winter"): (8, 30),
    ("em2", "supply_max"): (8, 82), ("em2", "supply_min"): (8, 82),
    ("fs1", "switch_on_runtime"): (0, 10), ("fs1", "frost_protection_limit"): (-20, 0),
}


@pytest.mark.parametrize("key, release", RELEASE_RANGES.items(), ids=lambda x: str(x))
def test_bounds_inside_the_release_range(key, release):
    setting = next(s for s in settings_of(DEVICE[key[0]]) if s.key == key[1])
    assert release[0] <= setting.minimum <= setting.maximum <= release[1]


@pytest.mark.parametrize("device, setting", all_settings(), ids=lambda x: getattr(x, "key", ""))
def test_guard_enforces_the_bounds_of_every_setting(device, setting):
    low, high = effective_bounds(setting, settings_of(device), {})
    assert (low, high) == (setting.minimum, setting.maximum)
    register_id = f"{device.key}:{setting.register}"
    for value in (low - setting.step, high + setting.step, low - 0.01, high + 0.01, float("nan")):
        with pytest.raises(WriteRefused) as refused:
            WriteGuard(True).check(register_id, value, low, high, None)
        assert refused.value.code == "out_of_bounds"
    for value in (low, high):
        WriteGuard(True).check(register_id, value, low, high, None)


def test_guard_enforces_linked_bounds():
    device = DEVICE["fs2"]
    by_key = {s.key: s for s in settings_of(device)}
    raw = {"0500": bytes.fromhex("d200"), "0800": bytes.fromhex("aa00"),  # normal 21.0, reduced 17.0
           "2800": bytes.fromhex("bc02"), "2b01": bytes.fromhex("c800")}  # flow max 70.0, flow min 20.0
    cases = [("room_reduced", 21.5, 21.0), ("room_normal", 16.5, 17.0), ("supply_min", 70.5, 70.0),
             ("supply_max", 19.5, 20.0)]
    for key, refused, accepted in cases:
        low, high = effective_bounds(by_key[key], settings_of(device), raw)
        with pytest.raises(WriteRefused):
            WriteGuard(True).check(f"fs2:{by_key[key].register}", refused, low, high, None)
        WriteGuard(True).check(f"fs2:{by_key[key].register}", accepted, low, high, None)


def test_values_ebusd_refuses_are_not_sent():
    # ebusd reads an integer type up to the first character and refuses an exponent ("1e-05"): so does the encoder
    setting = next(s for s in settings_of(DEVICE["fs1"]) if s.key == "switch_on_runtime")
    with pytest.raises(ValueError):
        setting.codec.encode(1e-05)
    assert setting.codec.encode(2.7) == bytes.fromhex("0200")  # as ebusd: integer part of "2.7"
