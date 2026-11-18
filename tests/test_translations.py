"""The translation files cover every key the code uses, in every language."""
import json
import string
from pathlib import Path

import pytest

from weishaupt_core.guard import REASONS
from weishaupt_core.registers import (DAYS, DEVICES, EM_READ_PARAMS, EM_SETTINGS, FS_CHOICES, FS_DATES,
                                      FS_READ_PARAMS, FS_SETTINGS, KA_CHOICES, KA_SETTINGS, PROGRAMS)

SRC = Path(__file__).resolve().parent.parent / "custom_components" / "weishaupt"
FILES = [SRC / "strings.json", *sorted((SRC / "translations").glob("*.json"))]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def leaves(node, prefix=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from leaves(value, f"{prefix}{key}.")
    else:
        yield prefix[:-1], node


def fields(text):
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_english_and_french_are_shipped():
    assert {p.name for p in FILES} >= {"strings.json", "en.json", "fr.json"}
    assert load(SRC / "strings.json") == load(SRC / "translations" / "en.json")


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_same_keys_and_placeholders_in_every_language(path):
    reference = dict(leaves(load(SRC / "strings.json")))
    other = dict(leaves(load(path)))
    assert other.keys() == reference.keys()
    for key, text in other.items():
        assert text.strip(), key
        assert fields(text) == fields(reference[key]), key


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_every_key_of_the_code_is_translated(path):
    data = load(path)
    entity = data["entity"]
    for setting in FS_SETTINGS + KA_SETTINGS + EM_SETTINGS:
        assert setting.key in entity["number"]
    for date in FS_DATES:
        assert date.key in entity["date"]
    for choice in FS_CHOICES + KA_CHOICES:
        assert set(choice.options.values()) == set(entity["select"][choice.key]["state"])
    for param in FS_READ_PARAMS + EM_READ_PARAMS:
        assert param.key in entity["sensor"]
        if param.options:
            assert set(param.options.values()) == set(entity["sensor"][param.key]["state"])
    for program in PROGRAMS:
        assert set(entity["sensor"][f"program_{program.key}"]["state_attributes"]) == set(DAYS)
    assert set(data["selector"]["day"]["options"]) == set(DAYS)
    assert "writes_enabled" in entity["switch"]
    assert {device.kind for device in DEVICES} | {"write_guard"} == set(data["device"])
    for code, text in REASONS.items():
        assert fields(data["exceptions"][code]["message"]) == fields(text), code


def test_device_names():
    by_key = {device.key: device for device in DEVICES}
    assert (by_key["ka"].kind, by_key["ka"].number, by_key["ka"].label) == ("ka", "", "KA")
    assert (by_key["fs2"].kind, by_key["fs2"].number, by_key["fs2"].label) == ("fs", "2", "FS2")
