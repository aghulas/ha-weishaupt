#!/usr/bin/env python3
"""Take the metadata of a release of the definitions into the integration and regenerate the translations.

The integration ships a verbatim copy of `weishaupt-metadata-<version>.json` (nothing is downloaded at run time)
and translation files generated from it. A new release of the definitions needs this script, not hand edits:

    scripts/vendor_metadata.py --release-dir /path/with/the/release/files --version 0.5.0
    scripts/vendor_metadata.py            # only regenerate translations/*.json from the vendored copy
    scripts/vendor_metadata.py --check    # fail when translations/*.json are not what would be generated

`--release-dir` holds the files of the release as downloaded from
https://github.com/aghulas/ebusd-configuration/releases (tag `weishaupt-<version>`): the metadata, the fixtures and
`sha256sums-<version>.txt`, against which both files are verified before they are copied.

The translation files are built from two sources: `scripts/translations/<lang>.json` (the texts of the
integration itself: configuration, repair issues, day names) and the metadata (device names, entity names, value
lists; the number entities of the writable settings take the names of their sensors). Only `scripts/translations/`
is edited by hand.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "custom_components" / "weishaupt"
SOURCES = ROOT / "scripts" / "translations"


def load_model_module():
    """`model.py` has no Home Assistant import: load it alone."""
    spec = importlib.util.spec_from_file_location("weishaupt_model", PACKAGE / "model.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def vendor(release_dir: Path, version: str) -> None:
    sums = {}
    for line in (release_dir / f"sha256sums-{version}.txt").read_text().splitlines():
        digest, _, name = line.partition(" ")
        sums[name.strip().lstrip("*")] = digest
    for name, target in ((f"weishaupt-metadata-{version}.json", PACKAGE / "metadata.json"),
                         (f"weishaupt-fixtures-{version}.json", ROOT / "tests" / "data" / "fixtures.json")):
        source = release_dir / name
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if sums.get(name) != digest:
            raise SystemExit(f"{name}: sha256 {digest}, the release says {sums.get(name)}")
        shutil.copyfile(source, target)
        print(f"{name}: checksum verified, copied to {target.relative_to(ROOT)}")


def translations(model_module, language: str) -> dict:
    model = model_module.Model.load(PACKAGE / "metadata.json")
    if language not in model.languages:
        raise SystemExit(f"the metadata has no language {language!r}")
    source = json.loads((SOURCES / f"{language}.json").read_text(encoding="utf-8"))
    weekdays, attributes = source.pop("weekdays"), source.pop("attributes")
    switch_name = source.pop("switch_name")
    number_suffix = source.pop("number_suffix")
    clock_names = {"en": "Clock offset of the installation", "fr": "Écart de l'horloge de l'installation"}
    button_names = {"en": "Set the clock from Home Assistant", "fr": "Régler l'horloge sur Home Assistant"}
    result = dict(source)
    result["device"] = {key: {"name": device.label[language]} for key, device in sorted(model.devices.items())}
    entity: dict[str, dict] = {"binary_sensor": {}, "number": {}, "select": {}, "sensor": {},
                               "switch": {"writes": {"name": switch_name}}}
    for description in model.value_entities:
        item = {"name": description.name[language]}
        if description.options:
            item["state"] = description.option_labels(language)
        entity[description.platform][description.translation_key] = item
    entity["text"] = {}
    for group in model.writable_programs:  # one text entity per program and day
        for number, day in enumerate(model_module.WEEKDAYS, 1):
            entity["text"][f"program_{group.id}_{day}"] = {
                "name": f"{group.label[language]} – {weekdays[day]}{number_suffix}"}
    entity["sensor"]["clock_offset"] = {"name": clock_names[language]}
    entity["button"] = {"set_clock": {"name": button_names[language]}}
    for description in model.setting_entities:  # the name of the sensor of its register, marked as the setting
        item = {"name": description.name[language] + number_suffix}
        if description.platform == "select":
            item["state"] = description.option_labels(language)
        entity[description.platform][description.translation_key] = item
    for description in model.group_entities:
        item = {"name": description.name[language]}
        if description.group.family == "program":
            item["state_attributes"] = {day: {"name": weekdays[day]} for day in model_module.WEEKDAYS}
            item["state_attributes"]["edited_on"] = {"name": {"en": "Edited on", "fr": "Modifié sur"}[language]}
        else:
            item["state_attributes"] = {key: {"name": text} for key, text in attributes.items()}
        entity["sensor"][description.translation_key] = item
    result["entity"] = {platform: dict(sorted(items.items())) for platform, items in entity.items()}
    return result


def icons(model_module) -> dict:
    """icons.json: icons for what has no device class to give one (programs, faults, counters, the clock, the
    write switch), by translation key, and the icon of the action."""
    model = model_module.Model.load(PACKAGE / "metadata.json")
    sensor: dict[str, dict] = {"clock_offset": {"default": "mdi:clock-alert-outline"}}
    for description in model.group_entities:
        family = description.group.family
        sensor[description.translation_key] = {
            "default": "mdi:calendar-week" if family == "program" else "mdi:alert-circle-outline"}
    for description in model.value_entities:
        if description.message.family == "fault_counter":
            sensor[description.translation_key] = {"default": "mdi:counter"}
    text = {f"program_{group.id}_{day}": {"default": "mdi:calendar-clock"}
            for group in model.writable_programs for day in model_module.WEEKDAYS}
    return {
        "entity": {
            "button": {"set_clock": {"default": "mdi:clock-edit-outline"}},
            "sensor": dict(sorted(sensor.items())),
            "switch": {"writes": {"default": "mdi:pencil-off", "state": {"on": "mdi:pencil"}}},
            "text": dict(sorted(text.items())),
        },
        "services": {"set_program": {"service": "mdi:calendar-edit"}},
    }


def render(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--release-dir", type=Path)
    parser.add_argument("--version")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.release_dir:
        if not args.version:
            parser.error("--release-dir needs --version")
        vendor(args.release_dir, args.version)
    model_module = load_model_module()
    stale = []
    for source in sorted(SOURCES.glob("*.json")):
        target = PACKAGE / "translations" / source.name
        text = render(translations(model_module, source.stem))
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != text:
                stale.append(target.name)
        else:
            target.write_text(text, encoding="utf-8")
            print(f"translations/{target.name}: written")
    target = PACKAGE / "icons.json"
    text = render(icons(model_module))
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            stale.append(target.name)
    else:
        target.write_text(text, encoding="utf-8")
        print("icons.json: written")
    if stale:
        raise SystemExit(f"not up to date: {', '.join(stale)} (run scripts/vendor_metadata.py)")


if __name__ == "__main__":
    main()
