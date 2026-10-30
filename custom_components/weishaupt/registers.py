"""Regulators and registers exposed by the integration.

Only registers whose write was tested on the école Sainte-Marie bus (30/10/2026) are listed. `source` is the address
the regulator accepts writes from: "ff" (address of the WCM-Diagnose service tool) for the settings, None (ebusd's own
address, 31) for registers the devices write to each other.

Bounds are the setting ranges of the Weishaupt manuals: WCM-FS 2.0 (83277701, 2012-04, parameter table p.21 and
§4.7) and WCM-KA 3.0 (83258401, 2013-04, p.50-63). The manuals give no step; 0.5 K and 1 % are the steps of their
display examples. `min_ref`/`max_ref` name a setting of the same device whose current value also bounds this one,
as the manuals describe (e.g. reduced room setpoint <= normal room setpoint).
"""
from __future__ import annotations

from dataclasses import dataclass

from .protocol import TEMP10, UNIT, Codec


@dataclass(frozen=True)
class Device:
    key: str
    zz: str  # slave address
    name: str


@dataclass(frozen=True)
class Setting:
    key: str
    register: str  # register and bank, hex "RRBB"
    name: str
    codec: Codec
    unit: str | None
    minimum: float
    maximum: float
    step: float
    source: str | None
    min_ref: str | None = None
    max_ref: str | None = None


@dataclass(frozen=True)
class DateSetting:
    """A date stored in three registers (day, month, 2-digit year)."""

    key: str
    registers: tuple[str, str, str]
    name: str
    source: str | None


DEVICES = [
    Device("ka", "15", "Cascade KA"),
    Device("fs1", "35", "Commande FS1"),
    Device("fs2", "75", "Commande FS2"),
    Device("fs3", "f5", "Commande FS3"),
]

FS_SETTINGS = [
    # FS 112, 113, 118, 117 (range of the "Universal" circuit type), 119
    Setting("room_normal", "0500", "Consigne ambiance normale", TEMP10, "°C", 16, 35, 0.5, "ff",
            min_ref="room_reduced"),
    Setting("room_reduced", "0800", "Consigne ambiance réduite", TEMP10, "°C", 10, 21.5, 0.5, "ff",
            max_ref="room_normal"),
    Setting("room_frost", "140a", "Consigne hors-gel", TEMP10, "°C", 4, 16, 0.5, "ff"),
    Setting("gradient", "0e01", "Pente de la courbe de chauffe", TEMP10, None, 2.5, 40, 0.5, "ff"),
    Setting("summer_winter", "1601", "Seuil été/hiver", TEMP10, "°C", 8, 30, 0.5, "ff"),
    # circuit flow limits, KA 342/341 (not in the FS manual): max up to 82 °C for the "Universal" type
    Setting("supply_max", "2800", "Température de départ maxi", TEMP10, "°C", 8, 82, 0.5, "ff",
            min_ref="supply_min"),
    Setting("supply_min", "2b01", "Température de départ mini", TEMP10, "°C", 8, 82, 0.5, "ff",
            max_ref="supply_max"),
]
FS_DATES = [
    DateSetting("holiday_from", ("1b01", "1c01", "1d01"), "Congés : début", "ff"),
    DateSetting("holiday_to", ("1e01", "1f01", "2001"), "Congés : fin", "ff"),
]
KA_SETTINGS = [
    # KA 342 (82 °C = value read, the maximum of the "Universal" type), 536, 535, 572 (max = 574 WW Maximal, 60 °C)
    Setting("supply_max", "2800", "Température de départ maxi", TEMP10, "°C", 8, 82, 0.5, "ff"),
    Setting("modulation_max", "eafd", "Modulation maxi", UNIT, "%", 30, 100, 1, "ff", min_ref="modulation_min"),
    Setting("modulation_min", "ebfd", "Modulation mini", UNIT, "%", 30, 100, 1, "ff", max_ref="modulation_max"),
    Setting("dhw_setpoint", "1300", "Consigne eau chaude", TEMP10, "°C", 40, 60, 0.5, "ff"),
]


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
    name: str

    def register(self, day: int, slot: int) -> str:
        """day 1 = Monday ... 7 = Sunday, slot 1-3."""
        return f"{day << 4 | (slot - 1):02x}{self.code}"


DAYS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")
PROGRAMS = [
    Program("heating_1", "14", "Programme chauffage 1"),
    Program("heating_2", "15", "Programme chauffage 2"),
    Program("heating_3", "16", "Programme chauffage 3"),
    Program("dhw", "17", "Programme eau chaude"),
    Program("circulation", "1a", "Programme circulation"),
]
# a slot of FS1 (heating 1, Monday, slot 1) was written and read back from ebusd's own address (30/10/2026)
PROGRAM_SOURCE = None


def program_registers() -> list[str]:
    return [p.register(d, s) for p in PROGRAMS for d in range(1, 8) for s in range(1, 4)]


def settings_of(device: Device) -> list[Setting]:
    return KA_SETTINGS if device.key == "ka" else FS_SETTINGS


def dates_of(device: Device) -> list[DateSetting]:
    return [] if device.key == "ka" else FS_DATES


def registers_of(device: Device) -> list[str]:
    """Every register to poll on a device."""
    regs = [s.register for s in settings_of(device)]
    for d in dates_of(device):
        regs.extend(d.registers)
    return regs
