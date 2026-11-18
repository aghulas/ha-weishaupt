"""Regulators and registers exposed by the integration.

Only registers whose WRITE was tested on the test installation bus (30/10/2026) are listed as writable
(Setting/Choice/DateSetting). `source` is the address the regulator accepts writes from: "ff" (address of the
WCM-Diagnose service tool) for the settings, None (ebusd's own address, 31) for registers the devices write to each
other.

Regulation parameters whose write is not yet bus-validated are exposed READ-ONLY first (READ_PARAMS, below), so their
value is visible while the write rule (source ff/31), the WCM-manual bounds and, for modes, the value table are being
checked register by register on the bus (step C). A read param becomes a Setting/Choice once its
write is validated.

Lot 1 (15/11/2026): a batch of regulation settings/choices is added with bounds from the WCM manuals
(WCM-FS 83277504, WCM-KA 83258404) and mode value tables from the ebusd templates (_16_CVariation, _16_HCType),
AHEAD of their per-register bus validation. Their `source` is "ff" by hypothesis (FS/KA settings). These writes stay
blocked by the integration's global write switch (CONF_WRITES_ENABLED) until each register is validated on the bus
(read / +1 step from ff / read back / restore) and writes are enabled. SwitchOnRuntime (anticipation) and RoomFactorI
are NOT in the manuals -> they stay read-only until their bounds are probed on the bus.

Bounds are the setting ranges of the Weishaupt manuals: WCM-FS 2.0 (83277701, 2012-04, parameter table p.21 and
§4.7) and WCM-KA 3.0 (83258401, 2013-04, p.50-63). The manuals give no step; 0.5 K and 1 % are the steps of their
display examples. `min_ref`/`max_ref` name a setting of the same device whose current value also bounds this one,
as the manuals describe (e.g. reduced room setpoint <= normal room setpoint).

Writes of numeric settings (0.1.1): raw `5023` telegrams, with the checksum computed by `protocol.py`, so that they
do not depend on the message names of the configuration ebusd loads. From 15/11/2026 to 0.1.0 they went through
ebusd message names; the raw telegram is byte for byte the one ebusd built from those definitions (same register,
encoding, source address and checksum). The bounds below are the only range check: the definitions of the older
configuration had none beyond the 16-bit type, and a release may not define the write at all.

Names shown to the user are not here: every `key` is a translation key of `strings.json` (entity names, and for
choices the option labels), translated in `translations/`.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .protocol import TEMP10, UNIT, Codec

TEMP1 = Codec(1)  # _16_Temp1: signed 16-bit integer, factor 1 (e.g. cascade change-over time in hours)


@dataclass(frozen=True)
class Device:
    key: str
    zz: str  # slave address

    @property
    def kind(self) -> str:
        """Translation key of the device name: ka, fs or em."""
        return self.key.rstrip("0123456789")

    @property
    def number(self) -> str:
        """Number of the device within its kind ("" for the only KA)."""
        return self.key[len(self.kind):]

    @property
    def label(self) -> str:
        """Short language-neutral name for logs and error messages, e.g. FS1."""
        return self.key.upper()


@dataclass(frozen=True)
class Setting:
    key: str
    register: str  # register and bank, hex "RRBB"
    codec: Codec
    unit: str | None
    minimum: float
    maximum: float
    step: float
    source: str | None
    min_ref: str | None = None
    max_ref: str | None = None
    # ebusd message name: write through the definition (`write -c`) instead of the raw 5023 frame; None -> raw hex.
    # Since 0.1.1 only the settings whose definition in the older configuration is a value list keep a name (see
    # NAMED_WRITES below); every other setting goes out raw, with the bytes ebusd built from its definition in 0.1.0.
    message: str | None = None


@dataclass(frozen=True)
class DateSetting:
    """A date stored in three registers (day, month, 2-digit year)."""

    key: str
    registers: tuple[str, str, str]
    source: str | None


DEVICES = [
    Device("ka", "15"),
    Device("fs1", "35"),
    Device("fs2", "75"),
    Device("fs3", "f5"),
    # Extension modules: circuits driven by an external boiler demand (relay on the H1 input).
    Device("em1", "50"),
    Device("em2", "51"),
    Device("em3", "52"),
]

FS_SETTINGS = [
    # FS 112, 113, 118, 117 (range of the "Universal" circuit type), 119
    Setting("room_normal", "0500", TEMP10, "°C", 16, 35, 0.5, "ff",
            min_ref="room_reduced"),
    Setting("room_reduced", "0800", TEMP10, "°C", 10, 21.5, 0.5, "ff",
            max_ref="room_normal"),
    Setting("room_frost", "140a", TEMP10, "°C", 4, 16, 0.5, "ff"),
    Setting("gradient", "0e01", TEMP10, None, 2.5, 40, 0.5, "ff"),
    Setting("summer_winter", "1601", TEMP10, "°C", 8, 30, 0.5, "ff"),
    # circuit flow limits, KA 342/341 (not in the FS manual): max up to 82 °C for the "Universal" type
    Setting("supply_max", "2800", TEMP10, "°C", 8, 82, 0.5, "ff",
            min_ref="supply_min"),
    Setting("supply_min", "2b01", TEMP10, "°C", 8, 82, 0.5, "ff",
            max_ref="supply_max"),
    # FS 132
    Setting("dhw_setpoint", "1300", TEMP10, "°C", 40, 60, 0.5, "ff"),
    # Lot 1 (fine regulation): WCM-FS bounds / ebusd codecs; source ff by hypothesis, AWAITING BUS VALIDATION
    # Still written by name (see NAMED_WRITES): P508, default 5
    Setting("room_factor_curve", "0f01", UNIT, None, 1, 20, 1, "ff",
            message="RoomFactorCurve"),
    Setting("boiler_mc_boost", "1101", TEMP10, "K", 0, 20, 0.5, "ff"),  # P424, default 2.0 K
    # Validated writable on the bus on 15/11. Maximum found by a bus sweep (10 kept, 20 rejected) -> 0..10 min.
    Setting("switch_on_runtime", "1001", UNIT, "min", 0, 10, 1, "ff"),
    # Lot 2 (15/11): frost protection limit (WCM-FS §6.5.28: off + -20..0 °C); bus-validated 0.0->-0.5->0.0 from ff.
    Setting("frost_protection_limit", "be02", TEMP10, "°C", -20, 0, 0.5, "ff"),
]
FS_DATES = [
    DateSetting("holiday_from", ("1b01", "1c01", "1d01"), "ff"),
    DateSetting("holiday_to", ("1e01", "1f01", "2001"), "ff"),
]
@dataclass(frozen=True)
class Choice:
    """A setting with a few named values."""

    key: str
    register: str
    options: dict[int, str]  # raw value -> option key (label in the translations)
    source: str | None


# FS 142: written and read back on FS1 (30/10/2026), 1 moved the room setpoint of a circuit on holiday from 4 to 14 °C
FS_CHOICES = [
    Choice("holiday_level", "3d01", {0: "frost", 1: "reduced"}, "ff"),
    # Lot 1: regulation modes; value tables = ebusd templates _16_OnOff/_16_CVariation/_16_HCType.
    # AWAITING BUS VALIDATION (source ff). hc_type is STRUCTURAL: changing the type reconfigures the circuit.
    Choice("adaption", "1501", {0: "off", 1: "on"}, "ff"),
    Choice("control_variation", "4101",
           {0: "constant", 1: "weather", 2: "weather_room", 3: "room"}, "ff"),
    Choice("hc_type", "7309",
           {0: "floor", 1: "floor_2", 2: "radiator_60", 3: "radiator_75", 4: "convector", 5: "universal"}, "ff"),
]


@dataclass(frozen=True)
class ReadParam:
    """A regulation register exposed READ-ONLY, ahead of its write validation on the bus (step C).

    `codec` decodes the raw 2 bytes for display only; `options` maps the raw integer of a mode register to a label
    (display only, no write). No bounds here: the writable entity (Setting/Choice, with the WCM-manual range) is
    added once the write of this register is tested on the bus. `register` = "RRBB"; `codec`/template from
    regulator.active.inc (ebusd-configuration-weishaupt)."""

    key: str
    register: str
    codec: Codec
    unit: str | None = None
    options: dict[int, str] | None = None


# Lot 1 (step B, 15/11/2026): anticipation / fine regulation, READ-ONLY. Codecs from the ebusd templates
# (regulator.active.inc). The write (bounds of the WCM manuals, source ff/31) is added register by register after
# its bus validation (step C).
# Still READ-ONLY: not documented in the WCM manuals (bounds to be probed on the bus before any write, step C).
# The 7 other Lot 1 parameters are writable (FS_SETTINGS/KA_SETTINGS/FS_CHOICES above).
FS_READ_PARAMS = [
    ReadParam("room_factor_i", "7109", UNIT),               # no P509 (FS 2.0 = P only)
]

KA_SETTINGS = [
    # KA 342 (82 °C = value read, the maximum of the "Universal" type), 536, 535, 572 (max = 574 WW Maximal, 60 °C)
    Setting("supply_max", "2800", TEMP10, "°C", 8, 82, 0.5, "ff"),
    # Still written by name (see NAMED_WRITES)
    Setting("modulation_max", "eafd", UNIT, "%", 30, 100, 1, "ff", min_ref="modulation_min",
            message="ModulationMax"),
    Setting("modulation_min", "ebfd", UNIT, "%", 30, 100, 1, "ff", max_ref="modulation_max",
            message="ModulationMin"),
    Setting("dhw_setpoint", "1300", TEMP10, "°C", 40, 60, 0.5, "ff"),
    # Lot 1: cascade power controller (WCM-KA); source ff by hypothesis, AWAITING BUS VALIDATION
    Setting("regulation_p", "9f02", UNIT, None, 10, 300, 1, "ff"),  # P539, default 100
    Setting("regulation_i", "9e02", UNIT, None, 10, 200, 1, "ff"),  # P540, default 100
    # Lot 2 hot water (15/11, WCM-KA §6.7.34/6.7.37): bus-validated from ff; DHWMaxLoad left out (no write definition).
    Setting("legionella_setup_temp", "8705", TEMP10, "°C", 40, 80, 0.5, "ff"),  # default 60 °C
    Setting("dhw_load_time", "8001", UNIT, "min", 0, 180, 10, "ff"),  # 0 = off; 10..180
    # Lot 2b (15/11): bus-validated from ff (WCM-KA §6.7.32 / §6.7.40).
    Setting("dhw_switch_diff", "4001", TEMP10, "K", -10, -1, 0.5, "ff"),  # -10..-1 K, default -3
    Setting("legionella_circ_time", "b109", UNIT, "s", 180, 1200, 60, "ff"),  # 3:00..20:00 min (in s)
    # Cascade (15/11): bus-validated from ff. Change-over time = rotation interval (h); blocking = anti-short-cycle.
    Setting("cascade_change_time", "ecfd", TEMP1, "h", 0, 250, 1, "ff"),  # 50 h; provisional range
    Setting("cascade_blocking_time", "2500", UNIT, "min", 0, 30, 1, "ff"),  # anti-short-cycle, 1 min; provisional range
    # Hydraulic separator / buffer (15/11, after the ebusd codec fix, x10). Validated writable from ff.
    # DeCoupleMax left out (not writable on the bus). Provisional bounds (the manual gives no clear range).
    Setting("decouple_min", "e7fd", TEMP10, "°C", 0, 50, 0.5, "ff"),  # 8.0 °C
    Setting("calorifier_switch_diff", "e2fd", TEMP10, "K", 1, 20, 0.5, "ff"),  # 2.0 K
]

# Lot 2 hot water: legionella protection modes (WCM-KA §6.7.36/6.7.39); bus-validated as no-op writes from ff.
KA_CHOICES = [
    Choice("dhw_legionella_day", "0101",
           {0: "off", 1: "monday", 2: "tuesday", 3: "wednesday", 4: "thursday", 5: "friday", 6: "saturday",
            7: "sunday"}, "ff"),
    Choice("circ_with_legionella", "f313", {0: "off", 1: "on"}, "ff"),
    # Cascade: boiler start order (WCM-KA §6.7.16). 0 = A, 1 = B, 240 = off. Bus-validated as no-op writes from ff.
    # Changing the order is a reconfiguration (to be done with the boilers off).
    Choice("boiler_seq_1", "cafd", {0: "a", 1: "b", 240: "off"}, "ff"),
    Choice("boiler_seq_2", "cbfd", {0: "a", 1: "b", 240: "off"}, "ff"),
]

# Circuits of the EM extension modules (em1, em2, em3). Same register codes as the FS (shared ebusd definitions);
# source validated on the bus on em2 (15/11): setpoints/gradient/summer-winter/frost from ff, flow maximum/minimum
# from 31 (None) on em2 and em3; em1 takes its flow limits from ff (EM1_SETTINGS below). Driven by an external boiler demand (relay on the H1 input).
EM_SETTINGS = [
    Setting("room_normal", "0500", TEMP10, "°C", 16, 35, 0.5, "ff",
            min_ref="room_reduced"),
    Setting("room_reduced", "0800", TEMP10, "°C", 10, 21.5, 0.5, "ff",
            max_ref="room_normal"),
    Setting("room_frost", "140a", TEMP10, "°C", 4, 16, 0.5, "ff"),
    Setting("gradient", "0e01", TEMP10, None, 2.5, 40, 0.5, "ff"),
    Setting("summer_winter", "1601", TEMP10, "°C", 8, 30, 0.5, "ff"),
    Setting("supply_max", "2800", TEMP10, "°C", 8, 82, 0.5, None,
            min_ref="supply_min"),     # source 31
    Setting("supply_min", "2b01", TEMP10, "°C", 8, 82, 0.5, None,
            max_ref="supply_max"),     # source 31
]
# em1 (address 50) is the system manager's own direct circuit: it acknowledges a flow maximum or minimum written from
# 31 but does not take it. Written from ff to 50, both were taken and 15 read the same value right after (proof
# writes of 18/11/2026: maximum 82.0 -> 81.5 -> 82.0, minimum 8.0 -> 8.5 -> 8.0, each acknowledged 00). So em1 writes
# its flow limits from ff; em2 and em3 keep 31 (proven).
EM1_SETTINGS = [replace(s, source="ff") if s.key in ("supply_max", "supply_min") else s for s in EM_SETTINGS]
# Boiler demand (external relay), read-only: H1Status (290a), value in the low byte.
EM_READ_PARAMS = [
    ReadParam("h1_demand", "290a", UNIT, options={0: "idle", 1: "demand"}),
]


# Settings left on the named write of 0.1.0 (`write -c <circuit> <Message>`). Their definition in the older
# configuration is a value list (`32768=Na`), so ebusd accepts only that entry and answers "element not found" to a
# number: the named write sends nothing, today and after a switch to a release (which has no such message). The
# telegram ebusd would send cannot be established from a definition or a capture, so they are not moved to raw hex.
NAMED_WRITES = {"ModulationMax", "ModulationMin", "RoomFactorCurve"}


def effective_bounds(setting: Setting, settings: list[Setting], raw: dict[str, bytes | None]) -> tuple[float, float]:
    """Bounds of a setting, narrowed by the current value of the settings it refers to (when known)."""
    by_key = {s.key: s for s in settings}
    low, high = setting.minimum, setting.maximum
    for ref, is_min in ((setting.min_ref, True), (setting.max_ref, False)):
        if ref is None or raw.get(by_key[ref].register) is None:
            continue
        value = by_key[ref].codec.decode(raw[by_key[ref].register])
        low, high = (max(low, value), high) if is_min else (low, min(high, value))
    return low, high


@dataclass(frozen=True)
class Program:
    """A time program: 7 days x 3 slots, register (day << 4 | slot - 1, program code)."""

    key: str
    code: str

    def register(self, day: int, slot: int) -> str:
        """day 1 = Monday ... 7 = Sunday, slot 1-3."""
        return f"{day << 4 | (slot - 1):02x}{self.code}"


DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
PROGRAMS = [
    Program("heating_1", "14"),
    Program("heating_2", "15"),
    Program("heating_3", "16"),
    Program("dhw", "17"),
    Program("circulation", "1a"),
]
# a slot of FS1 (heating 1, Monday, slot 1) was written and read back from ebusd's own address (30/10/2026)
PROGRAM_SOURCE = None


def program_registers() -> list[str]:
    return [p.register(d, s) for p in PROGRAMS for d in range(1, 8) for s in range(1, 4)]


def _is_em(device: Device) -> bool:
    return device.key.startswith("em")


def polls_programs(device: Device) -> bool:
    """The EM have no time program of their own (they follow the boiler demand): do not poll them."""
    return not _is_em(device)


def settings_of(device: Device) -> list[Setting]:
    if device.key == "ka":
        return KA_SETTINGS
    if device.key == "em1":
        return EM1_SETTINGS
    if _is_em(device):
        return EM_SETTINGS
    return FS_SETTINGS


def dates_of(device: Device) -> list[DateSetting]:
    return [] if (device.key == "ka" or _is_em(device)) else FS_DATES


def choices_of(device: Device) -> list[Choice]:
    if device.key == "ka":
        return KA_CHOICES
    if _is_em(device):
        return []
    return FS_CHOICES


def read_params_of(device: Device) -> list[ReadParam]:
    """Read-only params polled on a device."""
    if _is_em(device):
        return EM_READ_PARAMS
    return [] if device.key == "ka" else FS_READ_PARAMS


def registers_of(device: Device) -> list[str]:
    """Every register to poll on a device."""
    regs = ([s.register for s in settings_of(device)] + [c.register for c in choices_of(device)]
            + [p.register for p in read_params_of(device)])
    for d in dates_of(device):
        regs.extend(d.registers)
    return regs
