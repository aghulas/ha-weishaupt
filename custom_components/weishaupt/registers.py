"""Regulators and registers exposed by the integration.

Only registers whose WRITE was tested on the test installation bus (30/10/2026) are listed as writable
(Setting/Choice/DateSetting). `source` is the address the regulator accepts writes from: "ff" (address of the
WCM-Diagnose service tool) for the settings, None (ebusd's own address, 31) for registers the devices write to each
other.

Regulation parameters whose write is not yet bus-validated are exposed READ-ONLY first (READ_PARAMS, below), so their
value is visible while the write rule (source ff/31), the WCM-manual bounds and, for modes, the value table are being
checked register by register on the bus (étape C of the chantier). A read param becomes a Setting/Choice once its
write is validated.

Chantier Lot 1 (15/11/2026): a batch of regulation settings/choices is added with bounds from the WCM manuals
(WCM-FS 83277504, WCM-KA 83258404) and mode value tables from the ebusd templates (_16_CVariation, _16_HCType),
AHEAD of their per-register bus validation. Their `source` is "ff" by hypothesis (FS/KA settings). These writes stay
blocked by the integration's global write switch (CONF_WRITES_ENABLED) until each register is validated on the bus
(read / +1 step from ff / read back / restore) and writes are enabled. SwitchOnRuntime (anticipation) and RoomFactorI
are NOT in the manuals -> they stay read-only until their bounds are probed on the bus.

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
    message: str | None = None  # ebusd message name (write via definition instead of raw hex); None -> hex


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
            min_ref="room_reduced", message="RoomNormalTemp"),
    Setting("room_reduced", "0800", "Consigne ambiance réduite", TEMP10, "°C", 10, 21.5, 0.5, "ff",
            max_ref="room_normal", message="RoomSetbackTemp"),
    Setting("room_frost", "140a", "Consigne hors-gel", TEMP10, "°C", 4, 16, 0.5, "ff",
            message="RoomFrostProtectionTemp"),
    Setting("gradient", "0e01", "Pente de la courbe de chauffe", TEMP10, None, 2.5, 40, 0.5, "ff",
            message="GradientCurve"),
    Setting("summer_winter", "1601", "Seuil été/hiver", TEMP10, "°C", 8, 30, 0.5, "ff",
            message="SummerWinterChangeOverTemp"),
    # circuit flow limits, KA 342/341 (not in the FS manual): max up to 82 °C for the "Universal" type
    Setting("supply_max", "2800", "Température de départ maxi", TEMP10, "°C", 8, 82, 0.5, "ff",
            min_ref="supply_min", message="SupplyMaxTemp"),
    Setting("supply_min", "2b01", "Température de départ mini", TEMP10, "°C", 8, 82, 0.5, "ff",
            max_ref="supply_max", message="SupplyMinTemp"),
    # FS 132
    Setting("dhw_setpoint", "1300", "Consigne eau chaude", TEMP10, "°C", 40, 60, 0.5, "ff",
            message="DHWSetpoint"),
    # Lot 1 (régulation fine) — bornes WCM-FS / codecs ebusd ; source ff par hypothèse, EN ATTENTE DE VALIDATION BUS
    Setting("room_factor_curve", "0f01", "Facteur d'influence pièce (P)", UNIT, None, 1, 20, 1, "ff",
            message="RoomFactorCurve"),                                            # P508, défaut 5
    Setting("boiler_mc_boost", "1101", "Surélévation t° circuit mélangé (boost)", TEMP10, "K", 0, 20, 0.5, "ff",
            message="BoilerMCBoostTemp"),                                          # P424, défaut 2,0 K
    # Validé écrivable sur le bus le 15/11 (3->4->3 depuis ff). Absent des notices -> borne max PROVISOIRE (sweep à faire).
    Setting("switch_on_runtime", "1001", "Délai de relance (anticipation)", UNIT, "min", 0, 60, 1, "ff",
            message="SwitchOnRuntime"),
]
FS_DATES = [
    DateSetting("holiday_from", ("1b01", "1c01", "1d01"), "Congés : début", "ff"),
    DateSetting("holiday_to", ("1e01", "1f01", "2001"), "Congés : fin", "ff"),
]
@dataclass(frozen=True)
class Choice:
    """A setting with a few named values."""

    key: str
    register: str
    name: str
    options: dict[int, str]
    source: str | None


# FS 142: written and read back on FS1 (30/10/2026), 1 moved the room setpoint of a circuit on holiday from 4 to 14 °C
FS_CHOICES = [
    Choice("holiday_level", "3d01", "Congés : niveau de température", {0: "hors-gel", 1: "réduit"}, "ff"),
    # Lot 1 — modes de régulation ; tables de valeurs = gabarits ebusd _16_OnOff/_16_CVariation/_16_HCType.
    # EN ATTENTE DE VALIDATION BUS (source ff). ⚠️ hc_type est STRUCTUREL : changer le type reconfigure le circuit.
    Choice("adaption", "1501", "Adaptation", {0: "Arrêt", 1: "Marche"}, "ff"),
    Choice("control_variation", "4101", "Variante de régulation",
           {0: "Constant", 1: "Extérieur", 2: "Extérieur + ambiance", 3: "Ambiance"}, "ff"),
    Choice("hc_type", "7309", "Type de circuit de chauffage",
           {0: "Plancher", 1: "Plancher 2", 2: "Radiateur 60°", 3: "Radiateur 75°", 4: "Convecteur",
            5: "Universel"}, "ff"),
]


@dataclass(frozen=True)
class ReadParam:
    """A regulation register exposed READ-ONLY, ahead of its write validation on the bus (étape C).

    `codec` decodes the raw 2 bytes for display only; `options` maps the raw integer of a mode register to a label
    (display only, no write). No bounds here: the writable entity (Setting/Choice, with the WCM-manual range) is
    added once the write of this register is tested on the bus. `register` = "RRBB"; `codec`/template from
    regulator.active.inc (ebusd-configuration-weishaupt)."""

    key: str
    register: str
    name: str
    codec: Codec
    unit: str | None = None
    options: dict[int, str] | None = None


# Lot 1 (étape B, 15/11/2026) — anticipation / régulation fine, en LECTURE SEULE. Codecs d'après les gabarits ebusd
# (regulator.active.inc) ; les modes (_16_CVariation, _16_HCType) sont affichés en valeur brute tant que leur table
# n'est pas confirmée. L'écriture (bornes des notices WCM, source ff/31) s'ajoute registre par registre après
# validation bus (étape C).
# Restent en LECTURE SEULE : non documentés dans les notices WCM (bornes à sonder sur le bus avant écriture, étape C).
# Les 7 autres paramètres du Lot 1 sont promus en écrivables (FS_SETTINGS/KA_SETTINGS/FS_CHOICES ci-dessus).
FS_READ_PARAMS = [
    ReadParam("room_factor_i", "7109", "Facteur d'influence pièce (I)", UNIT),               # P509 absent (FS 2.0 = P seul)
]

KA_SETTINGS = [
    # KA 342 (82 °C = value read, the maximum of the "Universal" type), 536, 535, 572 (max = 574 WW Maximal, 60 °C)
    Setting("supply_max", "2800", "Température de départ maxi", TEMP10, "°C", 8, 82, 0.5, "ff",
            message="SupplyMaxTemp"),
    Setting("modulation_max", "eafd", "Modulation maxi", UNIT, "%", 30, 100, 1, "ff", min_ref="modulation_min",
            message="ModulationMax"),
    Setting("modulation_min", "ebfd", "Modulation mini", UNIT, "%", 30, 100, 1, "ff", max_ref="modulation_max",
            message="ModulationMin"),
    Setting("dhw_setpoint", "1300", "Consigne eau chaude", TEMP10, "°C", 40, 60, 0.5, "ff",
            message="DHWSetpoint"),
    # Lot 1 — régulateur de puissance de la cascade (WCM-KA) ; source ff par hypothèse, EN ATTENTE DE VALIDATION BUS
    Setting("regulation_p", "9f02", "Régulateur P (cascade)", UNIT, None, 10, 300, 1, "ff",
            message="RegulationP"),                                                # P539, défaut 100
    Setting("regulation_i", "9e02", "Régulateur I (cascade)", UNIT, None, 10, 200, 1, "ff",
            message="RegulationI"),                                                # P540, défaut 100
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


def choices_of(device: Device) -> list[Choice]:
    return [] if device.key == "ka" else FS_CHOICES


def read_params_of(device: Device) -> list[ReadParam]:
    """Read-only regulation params polled on a device (FS circuits for now; KA/EM come with their validation)."""
    return [] if device.key == "ka" else FS_READ_PARAMS


def registers_of(device: Device) -> list[str]:
    """Every register to poll on a device."""
    regs = ([s.register for s in settings_of(device)] + [c.register for c in choices_of(device)]
            + [p.register for p in read_params_of(device)])
    for d in dates_of(device):
        regs.extend(d.registers)
    return regs
