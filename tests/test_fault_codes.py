"""Fault code lists of the metadata (definitions 1.6.0 and later): a fault number looked up in the lists its field
names, shown with the codes the manual prints and a label; 0 and unknown numbers have none; a metadata without
the lists (1.5.0 and older) builds the same model without them."""
from __future__ import annotations

import copy
import json

from custom_components.weishaupt import faults
from custom_components.weishaupt.model import METADATA_FILE, CodeEntry, Model, fault_codes


def _data() -> dict:
    return json.loads(METADATA_FILE.read_text(encoding="utf-8"))


def _without_lists(data: dict) -> dict:
    data = copy.deepcopy(data)
    data.pop("vendor_code_lists", None)
    for message in data["messages"].values():
        for fld in message["fields"]:
            fld.pop("code_lists", None)
    return data


def _field(model: Model, key: str, name: str = "value"):
    return model.messages[key].field(name)


def test_lists_of_the_release():
    model = Model.load()
    assert sorted(model.code_lists) == ["wcm-faults", "wtc-gb-faults"]
    boiler, wcm = model.code_lists["wtc-gb-faults"], model.code_lists["wcm-faults"]
    assert (boiler.scheme, len(boiler.entries), min(boiler.entries), max(boiler.entries)) == ("wtc-gb", 44, 11, 89)
    assert (wcm.scheme, len(wcm.entries), min(wcm.entries), max(wcm.entries)) == ("wcm", 36, 130, 202)
    assert not set(boiler.entries) & set(wcm.entries)  # the lists of one field share no number
    assert boiler.entries[15] == CodeEntry(("W15", "F15"), {"en": "Flow/return difference too large",
                                                            "fr": "Écart départ/retour trop élevé"})
    # the fields that read a fault number name their lists, in order
    fields = {f"{m.key}/{f.name}": f.code_lists for m in model.messages.values() for f in m.fields if f.code_lists}
    assert len(fields) == 17
    assert fields["bc1/FaultHistorySlot1/number"] == fields["bc2/FaultHistorySlot6/number"] == ("wtc-gb-faults",)
    for key in ("em1/ErrorCode", "fs1/ErrorCode", "fs2/ErrorCode", "fs3/ErrorCode", "ka/ErrorStatus"):
        assert fields[f"{key}/value"] == ("wtc-gb-faults", "wcm-faults")


def test_a_number_is_looked_up_in_each_list_of_its_field():
    model = Model.load()
    pending = _field(model, "ka/ErrorStatus")
    assert model.fault_code(pending, 36).codes == ("F36",)  # boiler list
    assert model.fault_code(pending, 181).label["en"]  # WCM list
    assert model.fault_attributes(pending, 36, "en") == {
        "fault_code": "F36", "fault": "F36 – System water pressure too low"}
    assert model.fault_attributes(pending, 36, "fr") == {
        "fault_code": "F36", "fault": "F36 – Pression de l'installation trop faible"}
    assert model.fault_attributes(pending, 36, "de")["fault"] == "F36 – System water pressure too low"
    # a WCM fault log does not store the letter: a number that is both shows both codes
    assert model.fault_attributes(pending, 15, "en")["fault_code"] == "W15/F15"
    # a boiler slot only reads the boiler list
    slot = _field(model, "bc1/FaultHistorySlot1", "number")
    assert model.fault_code(slot, 36) is not None and model.fault_code(slot, 181) is None


def test_no_fault_unknown_numbers_and_other_fields_have_no_label():
    model = Model.load()
    pending = _field(model, "ka/ErrorStatus")
    for value in (0, 1, 99, 129, 203, None, "36", 36.0, True):
        assert model.fault_code(pending, value) is None, value
        assert model.fault_attributes(pending, value, "en") == {}
    supply = _field(model, "bc1/SupplyTemp")
    assert model.fault_attributes(supply, 36, "en") == {}  # a field that reads no fault number


def test_the_code_of_a_kind():
    both = CodeEntry(("W15", "F15"), {"en": "x"})
    assert (fault_codes(both), fault_codes(both, "warning"), fault_codes(both, "fault")) == ("W15/F15", "W15", "F15")
    assert fault_codes(CodeEntry(("F36",), {"en": "x"}), "warning") == "F36"  # the list prints F only
    assert fault_codes(CodeEntry(("181",), {"en": "x"}), "fault") == "181"


def test_history_and_fault_log_carry_the_label():
    model = Model.load()
    values = {"bc2/FaultHistorySlot1": "0;36;fault;BurnerOff;0;0;20;20;0.0;20",
              "bc2/FaultHistorySlot2": "0;99;fault;BurnerOff;0;0;20;20;0.0;20",
              "bc2/FaultHistorySlot3": "0;0;fault;BurnerOff;0;0;0;0;0.0;0"}
    for n in range(4, 7):
        values[f"bc2/FaultHistorySlot{n}"] = "0;0;fault;BurnerOff;0;0;0;0;0.0;0"
    values |= {"em1/ErrorId": "3", "em1/ErrorCode": "181", "em1/ErrorType": "10", "em1/ErrorDevice": "1",
               "em1/ErrorMinute": "30", "em1/ErrorHour": "3", "em1/ErrorDay": "7", "em1/ErrorMonth": "11",
               "em1/ErrorYear": "26"}
    reading = lambda key: tuple(values[key].split(";")) if key in values else None  # noqa: E731
    entries = faults.history(model, reading, model.groups["bc2/fault_history"], None)
    assert [(e["code"], e.get("label", {}).get("en")) for e in entries] == [
        ("F36", "System water pressure too low"), ("F99", None)]  # 99 is in no list: no label
    log = faults.log_entry(model, reading, "em1")
    assert log["code"] == 181 and log["fault"]["codes"] == "181" and log["fault"]["label"]["en"]
    values["em1/ErrorCode"] = "0"
    assert faults.log_entry(model, reading, "em1")["fault"] is None


def test_a_metadata_without_lists_builds_the_same_model():
    """1.5.0 and older: no `vendor_code_lists`, no `code_lists`; names, keys and entities are unchanged and no
    number has a label."""
    with_lists, without = Model.from_dict(_data()), Model.from_dict(_without_lists(_data()))
    assert without.code_lists == {}
    for attribute in ("value_entities", "setting_entities", "group_entities"):
        assert [(e.key, e.translation_key, e.name) for e in getattr(with_lists, attribute)] == [
            (e.key, e.translation_key, e.name) for e in getattr(without, attribute)]
    pending = _field(without, "ka/ErrorStatus")
    assert pending.code_lists == () and without.fault_attributes(pending, 36, "en") == {}
    reading = lambda key: ("0", "36", "fault", "BurnerOff", "0", "0", "0", "0", "0.0", "0")  # noqa: E731
    entries = faults.history(without, reading, without.groups["bc1/fault_history"], None)
    assert entries and all("label" not in e for e in entries)


def test_malformed_lists_and_entries_are_left_out():
    data = _data()
    data["vendor_code_lists"] = {
        "broken": "not a list",
        "partial": {"scheme": "wcm", "label": {"en": "Partial"}, "entries": {
            "140": {"codes": ["140"], "label": {"en": "Kept"}},
            "141": {"codes": [], "label": {"en": "No code"}},
            "x": {"codes": ["X"], "label": {"en": "Not a number"}},
            "142": {"codes": ["142"]}}}}
    model = Model.from_dict(data)
    assert list(model.code_lists) == ["partial"] and list(model.code_lists["partial"].entries) == [140]
    # the lists the fields name are not in this metadata: no label
    pending = _field(model, "ka/ErrorStatus")
    assert model.fault_code(pending, 140) is None  # "partial" is not one of its lists
    assert model.fault_code(pending, 36) is None  # its lists are gone
