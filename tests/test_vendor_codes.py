"""Vendor codes of the metadata (definitions 1.4.0 and later): read on messages and on fields, compared without case
and spaces, meaningful only with their scheme, absent from older metadata without harm."""
import copy
import json

from weishaupt_core.model import METADATA_FILE, Field, Model, VendorCode, code_key


def _data() -> dict:
    return json.loads(METADATA_FILE.read_text(encoding="utf-8"))


def _without_codes(data: dict) -> dict:
    data = copy.deepcopy(data)
    data.pop("vendor_schemes", None)
    data["open"].pop("vendor_codes", None)
    for message in data["messages"].values():
        message.pop("vendor_codes", None)
        for fld in message["fields"]:
            fld.pop("vendor_codes", None)
    return data


def test_codes_of_the_release():
    model = Model.load()
    assert sorted(model.vendor_schemes) == ["wcm", "wcm-fs-2", "wcm-ka-3", "wtc-gb"]
    boiler = model.vendor_schemes["wtc-gb"]
    assert boiler.label == {"en": "WTC-GB boiler automat", "fr": "Automate de la chaudière WTC-GB"}
    assert boiler.document == "83251704"
    # a message of one value carries its code itself
    hours = model.messages["bc1/BurnerServiceHours"]
    assert model.vendor_codes(hours, hours.fields[0]) == (VendorCode(
        "i46", "wtc-gb", "boiler manual 83251704, p. 47, menu Info"),)
    room = model.messages["fs1/RoomNormalTemp"]
    assert [(c.code, c.scheme) for c in model.vendor_codes(room, room.fields[0])] == [("P112", "wcm-fs-2")]
    # a message of several values carries them on its fields, not on itself
    counters = model.messages["bc1/Counters"]
    assert counters.vendor_codes == ()
    assert [c.code for c in model.vendor_codes(counters, counters.field("burnerhours"))] == ["i43"]
    assert model.vendor_codes(counters, counters.field("operatinghours")) == ()
    on_messages = [m for m in model.messages.values() if m.vendor_codes]
    on_fields = [(m, f) for m in model.messages.values() for f in m.fields if f.vendor_codes]
    assert (len(on_messages), len(on_fields)) == (197, 46)
    assert not any(m.vendor_codes and any(f.vendor_codes for f in m.fields) for m in model.messages.values())
    # every code names a scheme of the release; from 1.6.0 `wcm` numbers the fault codes of a code list only
    assert {c.scheme for m in on_messages for c in m.vendor_codes} | {
        c.scheme for _, f in on_fields for c in f.vendor_codes} == set(model.vendor_schemes) - {"wcm"}


def test_many_values_may_share_one_code():
    """A code is not a key: i31 is on FlueGasTemp and on the flue gas field of Temperatures, of both boilers."""
    model = Model.load()
    found = sorted(e.key for e in model.value_entities
                   if any(c.key == ("wtc-gb", "i31") for c in model.vendor_codes(e.message, e.field)))
    assert found == ["bc1/FlueGasTemp/value", "bc1/Temperatures/fluegastemp",
                     "bc2/FlueGasTemp/value", "bc2/Temperatures/fluegastemp"]


def test_codes_compare_without_case_and_spaces():
    assert code_key("P 31") == code_key("p31") == code_key(" P31 ") == "p31"
    assert code_key("I33") == code_key("i 33")
    assert VendorCode("P31", "wtc-gb").key == VendorCode("p 31", "wtc-gb").key
    assert VendorCode("P31", "wtc-gb").key != VendorCode("P31", "wtc-25-a").key  # another scheme: another value


def test_attributes_of_an_entity():
    model = Model.load()
    hours = model.messages["bc1/BurnerServiceHours"]
    assert model.code_attributes(hours, hours.fields[0], "fr") == {
        "vendor_code": "i46", "vendor_scheme": "Automate de la chaudière WTC-GB"}
    assert model.code_attributes(hours, hours.fields[0], "de")["vendor_scheme"] == "WTC-GB boiler automat"
    counters = model.messages["bc1/Counters"]
    assert model.code_attributes(counters, counters.field("operatinghours"), "en") == {}


def test_names_and_keys_do_not_depend_on_the_codes():
    """The codes are attributes: the entities, their keys and their names are those of the metadata without them."""
    with_codes, without = Model.from_dict(_data()), Model.from_dict(_without_codes(_data()))
    for attribute in ("value_entities", "setting_entities", "group_entities"):
        assert [(e.key, e.translation_key, e.name) for e in getattr(with_codes, attribute)] == [
            (e.key, e.translation_key, e.name) for e in getattr(without, attribute)]


def test_older_metadata_has_no_codes():
    model = Model.from_dict(_without_codes(_data()))
    assert model.vendor_schemes == {}
    assert not any(model.vendor_codes(e.message, e.field) for e in model.value_entities)
    hours = model.messages["bc1/BurnerServiceHours"]
    assert model.code_attributes(hours, hours.fields[0], "en") == {}


def test_unknown_scheme_and_malformed_entries():
    data = _data()
    data["vendor_schemes"]["broken"] = {"document": "1"}  # no label: left out
    data["messages"]["bc1/SupplyTemp"]["vendor_codes"] = [
        {"code": "X 7", "scheme": "later-scheme", "source": "a later manual"},
        {"code": "", "scheme": "wtc-gb"}, {"scheme": "wtc-gb"}, {"code": "P1"}, "P2", {"code": 3, "scheme": "wtc-gb"}]
    data["messages"]["bc1/ReturnTemp"]["vendor_codes"] = {"code": "i37"}  # not a list
    model = Model.from_dict(data)
    assert "broken" not in model.vendor_schemes
    supply = model.messages["bc1/SupplyTemp"]
    assert model.vendor_codes(supply, supply.fields[0]) == (VendorCode("X 7", "later-scheme", "a later manual"),)
    assert model.scheme_label("later-scheme") == {"en": "later-scheme"}
    assert model.code_attributes(supply, supply.fields[0], "fr") == {
        "vendor_code": "X 7", "vendor_scheme": "later-scheme"}
    ret = model.messages["bc1/ReturnTemp"]
    assert model.vendor_codes(ret, ret.fields[0]) == ()


def test_several_codes_and_a_register_read_by_two_messages():
    shipped = Model.load()
    em1 = shipped.messages["em1/RoomNormalTemp"]
    # from 1.4.1 the direct circuit has its own code: it wins over the message whose register it reads
    assert [c.code for c in shipped.vendor_codes(em1, em1.fields[0])] == ["112"]
    data = _data()
    data["messages"]["em1/RoomNormalTemp"].pop("vendor_codes", None)
    data["messages"]["ka/RoomNormalTemp"]["vendor_codes"] = [
        {"code": "501", "scheme": "wcm-ka-3", "source": "s"}, {"code": "P112", "scheme": "wcm-fs-2", "source": "s"},
        {"code": "502", "scheme": "wcm-ka-3", "source": "s"}]
    model = Model.from_dict(data)
    ka = model.messages["ka/RoomNormalTemp"]
    assert model.code_attributes(ka, ka.fields[0], "en") == {
        "vendor_code": "501, P112, 502",
        "vendor_scheme": "WCM-KA 3.0 system manager, WCM-FS 2.0 room unit and WCM-EM 2.1 module"}
    # em1/RoomNormalTemp reads the same register (same_as): it shows the codes of ka
    em1 = model.messages["em1/RoomNormalTemp"]
    assert em1.same_as == "ka/RoomNormalTemp" and em1.vendor_codes == ()
    assert [c.code for c in model.vendor_codes(em1, em1.fields[0])] == ["501", "P112", "502"]
    # the setting of that register gets them too
    setting = next(d for d in model.setting_entities if d.key in ("ka/RoomNormalTemp/value", "em1/RoomNormalTemp/value"))
    assert model.code_attributes(setting.message, setting.field, "en")["vendor_code"] == "501, P112, 502"


def test_a_field_code_wins_over_the_message():
    model = Model.load()
    message = model.messages["bc1/SupplyTemp"]
    fld = Field("value", "SIN", 0, "live", vendor_codes=(VendorCode("i99", "wtc-gb"),))
    assert [c.code for c in model.vendor_codes(message, fld)] == ["i99"]


def test_translations_name_the_code_attributes():
    root = METADATA_FILE.parent / "translations"
    model = Model.load()
    for language, names in (("en", ("Vendor code", "Vendor code scheme")),
                            ("fr", ("Code constructeur", "Numérotation du code constructeur"))):
        entity = json.loads((root / f"{language}.json").read_text(encoding="utf-8"))["entity"]
        for description in (*model.value_entities, *model.setting_entities):
            item = entity[description.platform][description.translation_key]
            if model.vendor_codes(description.message, description.field):
                assert (item["state_attributes"]["vendor_code"]["name"],
                        item["state_attributes"]["vendor_scheme"]["name"]) == names, description.key
