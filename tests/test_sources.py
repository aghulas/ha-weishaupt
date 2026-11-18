"""The source address of every write, as proven on the bus, in one table.

A regulator acknowledges a write from an address it does not take writes from, and ignores it: a wrong source is
not seen at write time, only in the read-back. This table is the reference; any change of source (or a new written
register) must change it too, deliberately. "31" stands for ebusd's own address (no `-s`).
"""
import pytest

from weishaupt_core.protocol import write_command
from weishaupt_core.registers import DEVICES, PROGRAM_SOURCE, choices_of, dates_of, settings_of

KA_NUMBERS = ("supply_max", "modulation_max", "modulation_min", "dhw_setpoint", "regulation_p", "regulation_i",
              "legionella_setup_temp", "dhw_load_time", "dhw_switch_diff", "legionella_circ_time",
              "cascade_change_time", "cascade_blocking_time", "decouple_min", "calorifier_switch_diff")
KA_CHOICES = ("dhw_legionella_day", "circ_with_legionella", "boiler_seq_1", "boiler_seq_2")
FS_NUMBERS = ("room_normal", "room_reduced", "room_frost", "gradient", "summer_winter", "supply_max", "supply_min",
              "dhw_setpoint", "room_factor_curve", "boiler_mc_boost", "switch_on_runtime", "frost_protection_limit")
FS_CHOICES = ("holiday_level", "adaption", "control_variation", "hc_type")
FS_DATES = ("holiday_from", "holiday_to")
EM_FF = ("room_normal", "room_reduced", "room_frost", "gradient", "summer_winter")


def table():
    expected = {("ka", "number", k): "ff" for k in KA_NUMBERS}
    expected |= {("ka", "select", k): "ff" for k in KA_CHOICES}
    for fs in ("fs1", "fs2", "fs3"):
        expected |= {(fs, "number", k): "ff" for k in FS_NUMBERS}
        expected |= {(fs, "select", k): "ff" for k in FS_CHOICES}
        expected |= {(fs, "date", k): "ff" for k in FS_DATES}
    for em in ("em1", "em2", "em3"):
        expected |= {(em, "number", k): "ff" for k in EM_FF}
    # flow limits of the modules: 31 proven on em2 (15/11) and em3; em1, the system manager's direct circuit,
    # acknowledges them from 31 without taking them; written from ff to 50 they were taken (18/11, 0.1.3)
    expected |= {("em1", "number", "supply_max"): "ff", ("em1", "number", "supply_min"): "ff",
                 ("em2", "number", "supply_max"): "31", ("em2", "number", "supply_min"): "31",
                 ("em3", "number", "supply_max"): "31", ("em3", "number", "supply_min"): "31"}
    return expected


def actual():
    found = {}
    for device in DEVICES:
        for kind, items in (("number", settings_of(device)), ("select", choices_of(device)),
                            ("date", dates_of(device))):
            for item in items:
                key = (device.key, kind, item.key)
                assert key not in found, key
                found[key] = item.source or "31"
    return found


def test_every_written_register_has_the_source_of_the_table():
    assert actual() == table()


def test_program_slots_from_31():
    assert PROGRAM_SOURCE is None  # a slot written and read back from ebusd's own address (30/10/2026)


@pytest.mark.parametrize("key", ["supply_max", "supply_min"])
def test_em1_flow_limits_go_out_from_ff(key):
    em1 = next(d for d in DEVICES if d.key == "em1")
    setting = next(s for s in settings_of(em1) if s.key == key)
    assert write_command(em1.zz, setting.register, setting.codec.encode(45.0), setting.source).startswith(
        "hex -s ff 505023")


@pytest.mark.parametrize("module", ["em2", "em3"])
def test_em2_em3_flow_limits_unchanged_from_31(module):
    device = next(d for d in DEVICES if d.key == module)
    for setting in settings_of(device):
        if setting.key in ("supply_max", "supply_min"):
            assert write_command(device.zz, setting.register, setting.codec.encode(45.0), setting.source).startswith(
                f"hex {device.zz}5023")
