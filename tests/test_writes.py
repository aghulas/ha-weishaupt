"""What may be written and the bytes of a write, against the bus captures of the definitions release and the
answers a real ebusd gave (fork build with the run-time checksum, and a stock build) to the same commands."""
import json
from collections import Counter
from pathlib import Path

import pytest

from fake_ebusd import FakeEbusd
from weishaupt_core.ebusd import Definition, FieldDefinition, parse_definitions
from weishaupt_core.model import Model
from weishaupt_core.model import single_setting
from weishaupt_core.writes import capability, crc, linked, round_half_away, write_specs


@pytest.fixture(scope="module")
def model():
    return Model.load()


@pytest.fixture(scope="module")
def loaded(golden):
    return {circuit: parse_definitions(text) for circuit, text in golden["write_definitions"].items()}


@pytest.fixture(scope="module")
def specs(model, loaded):
    specs, refused, placeholders = write_specs(model, loaded)
    # settings whose meaning is not established carry no range (since definitions 0.5.11): read only
    assert sorted((r.key, r.reason) for r in refused if r.exposed) == sorted(
        (f"{room}/{name}", "no range") for room in ("fs1", "fs2", "fs3")
        for name in ("ControlVariation", "HolidayStartThird", "HolidayEndThird"))
    # program slots and the date and time broadcast: writable in the definitions, not offered here
    assert len([r for r in refused if not r.exposed]) == 253
    return specs


@pytest.fixture(scope="module")
def captured():
    from conftest import DATA
    return [r for r in json.loads((DATA / "fixtures.json").read_text())["readings"] if r["type"] == "write"]


def test_exactly_the_settings_the_metadata_marks_writable(model, specs):
    """83 settings of one value: 78 numbers and 5 choices (legionella day and circulation of ka, holiday
    temperature level of the three room units). Nine more are marked writable but carry no range, their meaning not
    established: read only. From definitions 0.6.0 the setback and frost protection temperatures of room unit 2
    have no write line (the room unit shares the store of em1). The program slots and the date and time broadcast
    are writable in the definitions and not offered by this version."""
    marked = {key for key, message in model.messages.items() if single_setting(message) is not None}
    assert set(specs) == {key for key in marked if not key.endswith(("ControlVariation", "Third"))}
    assert len(specs) == 83 and "fs2/RoomSetbackTemp" not in specs and "fs2/RoomFrostProtectionTemp" not in specs
    assert {key for key, spec in specs.items() if spec.values} == {
        "ka/DHWLegionellaDay", "ka/CircWithLegionella", "fs1/HolidayTempLevel", "fs2/HolidayTempLevel",
        "fs3/HolidayTempLevel"}
    # the classes of the metadata, as they are: normal and setback room temperature and hot-water setpoint are
    # comfort on every device that has a write (15), the rest regulation
    assert Counter(spec.risk for spec in specs.values()) == {"regulation": 68, "comfort": 15}
    assert {key.split("/")[1] for key, spec in specs.items() if spec.risk == "comfort"} == {
        "RoomNormalTemp", "RoomSetbackTemp", "DHWSetpoint"}
    for key, spec in specs.items():
        assert spec.risk == model.messages[key].write.risk, key
    # eleven settings have no range in the CSV (fractional bounds): the range of their write conditions in the
    # metadata, with its source; the integration holds no range of its own (the twelfth, the setback temperature
    # of room unit 2, is no longer written from definitions 0.6.0)
    from_metadata = {key: (s.minimum, s.maximum, s.step) for key, s in specs.items() if s.bounds_from == "metadata"}
    assert len(from_metadata) == 11
    for key, bounds in from_metadata.items():
        conditions = model.messages[key].write
        assert bounds == (conditions.minimum, conditions.maximum, conditions.step) and specs[key].range_source
    assert {v for k, v in from_metadata.items() if k.endswith("/RoomSetbackTemp")} == {(10.0, 21.5, 0.5)}
    assert {v for k, v in from_metadata.items() if k.endswith("/GradientCurve")} == {(2.5, 40.0, 0.5)}
    for spec in specs.values():  # every other bound and step is the field's
        fld = model.messages[spec.key].fields[0]
        if spec.bounds_from == "definitions" and spec.values is None:
            assert (spec.minimum, spec.maximum) == (fld.minimum, fld.maximum)
            assert spec.step == (fld.step or 1)


def test_every_setting_has_the_source_of_its_metadata(model, specs):
    """The source address comes from the metadata, setting by setting; nothing in the integration decides it. The
    flow limits of the system manager's own circuit (em1) are taken from ff only, those of the heating modules
    (em2, em3) from 31."""
    for key, spec in specs.items():
        source = model.messages[key].write.source
        assert spec.source == source, key
        assert spec.ebusd_source == ("ff" if source == "ff" else None), key
    assert {key for key, spec in specs.items() if spec.source == "31"} == {
        "em2/SupplyMaxTemp", "em2/SupplyMinTemp", "em3/SupplyMaxTemp", "em3/SupplyMinTemp"}
    assert specs["em1/SupplyMaxTemp"].source == specs["em1/SupplyMinTemp"].source == "ff"


def test_the_source_follows_the_metadata_when_it_changes(model, loaded):
    """A metadata that gave another source would be followed: the integration holds no table of sources."""
    import dataclasses
    message = model.messages["em1/SupplyMaxTemp"]
    changed = dataclasses.replace(message, write=dataclasses.replace(message.write, source="31"))
    model2 = dataclasses.replace(model, messages=model.messages | {message.key: changed})
    specs, _, _ = write_specs(model2, loaded)
    assert specs["em1/SupplyMaxTemp"].ebusd_source is None and specs["em2/SupplyMaxTemp"].source == "31"


def test_every_captured_write_telegram_is_built_byte_for_byte(specs, captured):
    """The telegram built for each setting equals the ones captured on the bus (change and restore), for all 71
    settings, from the source the capture shows. A choice is given by the ebusd name of its entry."""
    covered = set()
    for reading in captured:
        key = f"{reading['circuit']}/{reading['message']}"
        if key not in specs:  # a program slot or the date and time broadcast: not offered here
            continue
        spec = specs[key]
        value = reading["decoded"]["value"]
        if spec.values is not None:
            value = spec.raw_of_text(value)
        expected = f"{reading['zz']}5023{len(reading['master'].split()):02x}{reading['master'].replace(' ', '')}"
        assert spec.telegram(value) == expected, key
        assert spec.source == reading["qq"] and spec.zz == reading["zz"]
        assert spec.on_step(value)
        covered.add(key)
    assert covered == set(specs)
    assert sum(1 for r in captured if f"{r['circuit']}/{r['message']}" in specs) == 146


def test_the_changes_of_the_telegram_log(specs):
    """Change and restore telegrams of evidence/settings-writes.md (telegram log of the installation)."""
    log = {"ka/BlockingTime": (2, "cc25000200"), "ka/ChangeOverTime": (51, "88ecfd3300"),
           "ka/DeCoupleMinTemp": (8.5, "00e7fd5500"), "ka/CalorifierSwitchDiff": (2.5, "24e2fd1900"),
           "ka/DHWSwitchDiff": (-5.5, "774001c9ff"), "ka/DHWLoadTime": (10, "7080010a00"),
           "ka/LegionellaSetpoint": (60.5, "0287055d02"), "ka/LegionellaCirculationTime": (660, "bab1099402"),
           "ka/RegulationP": (101, "c49f026500"), "ka/RegulationI": (101, "cc9e026500"),
           "fs1/SwitchOnRuntime": (4, "1010010400"), "fs1/FrostProtectionLimitTemp": (-0.5, "e3be02fbff"),
           "fs1/BoilerMCBoostTemp": (2.5, "8011011900"), "fs1/RoomFrostProtectionTemp": (8.5, "ac140a5500"),
           "em2/RoomNormalTemp": (22, "640500dc00"), "em2/RoomSetbackTemp": (21, "c00800d200"),
           "em2/RoomFrostProtectionTemp": (10.5, "54140a6900"), "em2/GradientCurve": (10.5, "8c0e016900"),
           "em2/SummerWinterChangeOverTemp": (20.5, "ac1601cd00"), "em2/SupplyMaxTemp": (75.5, "fe2800f302"),
           "em2/SupplyMinTemp": (8.5, "002b015500"), "em3/GradientCurve": (10.5, "8c0e016900")}
    assert set(log) <= set(specs)
    for key, (value, data) in log.items():
        assert specs[key].telegram(value)[8:] == data, key


def test_encoding():
    assert round_half_away(212.5) == 213 and round_half_away(-212.5) == -213
    assert crc(bytes.fromhex("25000100")) == 0x28


def test_a_value_outside_its_type_is_not_encoded(specs):
    with pytest.raises(ValueError):
        specs["ka/RegulationP"].raw(70000)
    with pytest.raises(ValueError):
        specs["ka/BlockingTime"].raw(-1)


def test_steps(specs):
    spec = specs["ka/DHWLoadTime"]
    assert spec.on_step(170) and not spec.on_step(175)
    assert specs["em2/RoomNormalTemp"].on_step(21.5) and not specs["em2/RoomNormalTemp"].on_step(21.3)


def test_linked_settings(specs):
    assert linked(specs["em2/RoomNormalTemp"], specs) == (specs["em2/RoomSetbackTemp"], None)
    assert linked(specs["em2/RoomSetbackTemp"], specs) == (None, specs["em2/RoomNormalTemp"])
    assert linked(specs["em2/SupplyMinTemp"], specs) == (None, specs["em2/SupplyMaxTemp"])
    assert linked(specs["ka/ModulationMax"], specs) == (specs["ka/ModulationMin"], None)
    assert linked(specs["ka/ModulationMin"], specs) == (None, specs["ka/ModulationMax"])
    assert linked(specs["ka/BlockingTime"], specs) == (None, None)


def _definition(**changes) -> Definition:
    base = dict(direction="w", circuit="ka", name="BlockingTime", comment="[WCRC] x",
                fields=(FieldDefinition("value", "m", "UIN", "", "min"),), zz="15", pbsb="5023", id="4c2500")
    return Definition(**(base | changes))


@pytest.mark.parametrize("changes", [
    {"comment": "no marker"}, {"pbsb": "5022"}, {"zz": "35"}, {"id": "4c25"},
    {"fields": (FieldDefinition("value", "m", "SIN", "", "min"),)},
    {"fields": (FieldDefinition("value", "m", "UIN", "10", "min"),)}, {"direction": "r"}])
def test_a_write_definition_that_differs_leaves_the_setting_read_only(model, changes):
    specs, refused, _ = write_specs(model, {"ka": [_definition(**changes)]})
    assert "ka/BlockingTime" not in specs
    assert "ka/BlockingTime" in {r.key for r in refused}
    assert write_specs(model, {"ka": [_definition()]})[0]["ka/BlockingTime"].register == "2500"


def test_structural_settings_are_never_writable(model):
    """The settings the evidence calls structural or awaiting a decision have no write conditions."""
    for key in ("ka/DHWLoadingPriority", "ka/ModulationStatus", "fs1/ControlVariationMode"):
        if key in model.messages:
            assert not model.messages[key].writable


@pytest.mark.parametrize("build", ["fork", "stock"])
def test_the_simulation_answers_writes_as_the_real_ebusd(golden, build):
    """762 write commands asked of the real ebusd without a bus (scripts/capture_ebusd.py): the simulated ebusd
    gives the same answer to each, for the fork's build and for a stock one. Without a bus a matched telegram ends
    in `no signal`: it would have been sent."""
    fake = FakeEbusd(golden)
    fake.runtime_checksum = build == "fork"
    fake.signal = False
    recorded = golden["writes"][build]
    assert len(recorded) == 762
    for command, answer in recorded.items():
        assert fake.answer(command) == answer, command
    assert fake.writes == []


@pytest.mark.parametrize("build,expected", [("fork", "present"), ("stock", "absent")])
def test_the_probe_of_the_run_time_checksum(golden, specs, build, expected):
    """The two probes the integration sends, with the answers the real builds gave: neither is sent to the bus."""
    answers = golden["writes"][build]
    spec = specs["ka/BlockingTime"]
    placeholder = "4c"
    correct = f"write -c weishaupt-probe -h {spec.telegram(1)}"
    other = f"write -c weishaupt-probe -h {spec.placeholder_telegram(1, placeholder)}"
    simple = {"ERR: invalid argument": "matched", "ERR: element not found": "not found"}
    assert capability(simple[answers[correct]], simple[answers[other]]) == expected
    assert capability("matched", "matched") == capability("error", "not found") == "unknown"


def test_a_setting_without_any_range_stays_read_only(model, loaded):
    """Neither the field nor the write conditions give a range (a metadata older than 0.5.5): not writable. The
    integration supplies no range of its own."""
    import dataclasses
    message = model.messages["em2/RoomSetbackTemp"]
    write = dataclasses.replace(message.write, minimum=None, maximum=None, step=None, range_source=None)
    changed = dataclasses.replace(message, write=write)
    specs, refused, _ = write_specs(dataclasses.replace(model, messages=model.messages | {message.key: changed}),
                                    loaded)
    assert "em2/RoomSetbackTemp" not in specs
    assert ("em2/RoomSetbackTemp", "no range") in [(r.key, r.reason) for r in refused if r.exposed]


def test_a_range_of_the_field_comes_before_the_write_conditions(model, loaded):
    import dataclasses
    message = model.messages["em2/RoomSetbackTemp"]
    fld = dataclasses.replace(message.fields[0], minimum=12, maximum=20, step=0.5)
    changed = dataclasses.replace(message, fields=(fld,))
    specs, _, _ = write_specs(dataclasses.replace(model, messages=model.messages | {message.key: changed}), loaded)
    spec = specs["em2/RoomSetbackTemp"]
    assert (spec.minimum, spec.maximum, spec.bounds_from, spec.range_source) == (12, 20, "definitions", None)
