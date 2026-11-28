"""What the MQTT bridge builds from the metadata alone: the readings of a bridge payload, and which settings and
programs it offers to write (the same rules as with ebusd: proven, kept by this device, read, one 16-bit number)."""
from __future__ import annotations

import copy
import json

from custom_components.weishaupt.model import METADATA_FILE, Model
from custom_components.weishaupt.mqtt_bridge import (_decode_mqtt_message, _mqtt_program_specs,
                                                       _mqtt_write_specs)

DATA = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
SETTING, PROGRAM = "ka/DHWSetpoint", "fs1/heating1"


def _model(change=None) -> Model:
    data = copy.deepcopy(DATA)
    if change is not None:
        change(data)
    return Model.from_dict(data)


def _all(model: Model) -> set[str]:
    return set(model.messages)


def _circuits(model: Model) -> set[str]:
    return {m.circuit for m in model.messages.values()}


def test_a_payload_becomes_the_fields_of_a_reading():
    model = _model()
    demand = model.messages["bc1/PowerDemand"]  # several values, one of them skipped
    values = _decode_mqtt_message(demand, {f.name: 7 for f in demand.fields})
    assert len(values) == len(demand.fields) and "" in values
    assert all(v == "" for v, f in zip(values, demand.fields) if f.skip and not f.guard)
    counters = model.messages["bc1/FaultCounters1"]  # its first answer byte is a guard: always 0 once decoded
    values = _decode_mqtt_message(counters, {f.name: 3 for f in counters.fields})
    assert values[0] == "0" and counters.fields[0].guard and set(values[1:]) == {"3"}
    # a bare value where several are expected: none of them is known
    assert all(v == "-" for v, f in zip(_decode_mqtt_message(demand, 7), demand.fields) if f.shown)
    supply = model.messages["bc1/SupplyTemp"]  # one value: the bare value is it
    assert _decode_mqtt_message(supply, 42.5) == ("42.5",)


def test_settings_offered_for_writing():
    model = _model()
    specs, refused = _mqtt_write_specs(model, _circuits(model), _all(model))
    assert SETTING in specs and SETTING not in refused
    # read from another device's store: changed there
    shared = _model(lambda d: d["messages"][SETTING].update(shared_with="em1/DHWSetpoint"))
    specs, refused = _mqtt_write_specs(shared, _circuits(shared), _all(shared))
    assert SETTING not in specs and refused[SETTING].startswith("kept by em1/DHWSetpoint")
    # not read on this bus
    specs, refused = _mqtt_write_specs(model, _circuits(model), _all(model) - {SETTING})
    assert SETTING not in specs and refused[SETTING] == "not usable"
    # a risk class or a source this version does not write
    risky = _model(lambda d: d["messages"][SETTING]["write"].update(risk="structural"))
    specs, refused = _mqtt_write_specs(risky, _circuits(risky), _all(risky))
    assert SETTING not in specs and refused[SETTING] == "unsupported risk/source (structural/ff)"
    # not one 16-bit number
    wide = _model(lambda d: d["messages"][SETTING]["fields"][0].update(type="ULG"))
    specs, refused = _mqtt_write_specs(wide, _circuits(wide), _all(wide))
    assert refused[SETTING] == "not one 16-bit number"


def test_programs_offered_for_writing():
    model = _model()
    members = model.groups[PROGRAM].members

    def offered(other: Model, usable: set[str] | None = None) -> bool:
        programs, slots = _mqtt_program_specs(other, _circuits(other), _all(other) if usable is None else usable)
        return any(key in slots for key in members)

    assert offered(model)
    # a member the metadata does not describe
    assert not offered(_model(lambda d: d["messages"].pop(members[0])))
    # a member read from another device's store
    assert not offered(_model(lambda d: d["messages"][members[0]].update(shared_with="fs2/HCProgramMon1")))
    # a member whose write is a regulation setting, not a comfort one
    assert not offered(_model(lambda d: d["messages"][members[0]]["write"].update(risk="regulation")))
    # a member not read on this bus
    assert not offered(model, _all(model) - {members[0]})
