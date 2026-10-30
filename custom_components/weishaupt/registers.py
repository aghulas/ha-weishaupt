"""Regulators and registers exposed by the integration.

Only registers whose write was tested on the école Sainte-Marie bus (30/10/2026) are listed. `source` is the address
the regulator accepts writes from: "ff" (address of the WCM-Diagnose service tool) for the settings, None (ebusd's own
address, 31) for registers the devices write to each other. Bounds are provisional: to be checked against the
Weishaupt manuals and the commissioning values before the writes are enabled.
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
    Setting("room_normal", "0500", "Consigne ambiance normale", TEMP10, "°C", 10, 26, 0.5, "ff"),
    Setting("room_reduced", "0800", "Consigne ambiance réduite", TEMP10, "°C", 5, 20, 0.5, "ff"),
    Setting("room_frost", "140a", "Consigne hors-gel", TEMP10, "°C", 2, 10, 0.5, "ff"),
    Setting("gradient", "0e01", "Pente de la courbe de chauffe", TEMP10, None, 2.5, 40, 0.5, "ff"),
    Setting("summer_winter", "1601", "Seuil été/hiver", TEMP10, "°C", 10, 25, 0.5, "ff"),
    Setting("supply_max", "2800", "Température de départ maxi", TEMP10, "°C", 30, 80, 0.5, "ff"),
    Setting("supply_min", "2b01", "Température de départ mini", TEMP10, "°C", 5, 40, 0.5, "ff"),
]
FS_DATES = [
    DateSetting("holiday_from", ("1b01", "1c01", "1d01"), "Congés : début", "ff"),
    DateSetting("holiday_to", ("1e01", "1f01", "2001"), "Congés : fin", "ff"),
]
KA_SETTINGS = [
    Setting("supply_max", "2800", "Température de départ maxi", TEMP10, "°C", 50, 85, 0.5, "ff"),
    Setting("modulation_max", "eafd", "Modulation maxi", UNIT, "%", 50, 100, 1, "ff"),
    Setting("modulation_min", "ebfd", "Modulation mini", UNIT, "%", 20, 50, 1, "ff"),
    Setting("dhw_setpoint", "1300", "Consigne eau chaude", TEMP10, "°C", 40, 60, 0.5, "ff"),
]


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
