"""What HACS and Home Assistant ask of the files of the repository.

The HACS validation action only looks at a pushed repository. These tests apply the same rules to the local
files (rules read in custom_components/hacs/validate of hacs/integration): the keys of hacs.json, the keys of
the manifest, a README, a local brand icon. What HACS asks of the repository itself on GitHub (description,
topics, issues enabled, licence) cannot be tested here.
"""
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "custom_components" / "weishaupt"
HACS_KEYS = {"name", "content_in_root", "hide_default_branch", "render_readme", "zip_release", "filename", "hacs",
             "homeassistant", "persistent_directory", "country"}


def test_hacs_json():
    data = json.loads((ROOT / "hacs.json").read_text())
    assert isinstance(data["name"], str) and data["name"]
    assert set(data) <= HACS_KEYS  # HACS refuses any other key
    assert re.fullmatch(r"\d{4}\.\d{1,2}\.\d+", data["homeassistant"])


def test_manifest():
    manifest = json.loads((PACKAGE / "manifest.json").read_text())
    for key in ("codeowners", "documentation", "domain", "issue_tracker", "name", "version"):  # HACS
        assert manifest[key], key
    assert manifest["domain"] == "weishaupt" == PACKAGE.name
    assert manifest["config_flow"] is True
    assert (manifest["integration_type"], manifest["iot_class"]) == ("hub", "local_polling")
    assert manifest["requirements"] == []  # nothing installed from outside
    assert manifest["documentation"].startswith("https://") and manifest["issue_tracker"].startswith("https://")
    assert re.fullmatch(r"\d+\.\d+\.\d+((b|rc)\d+)?", manifest["version"])
    assert json.loads((ROOT / "hacs.json").read_text())["name"] == manifest["name"]


def test_readme_and_licence():
    assert (ROOT / "README.md").stat().st_size > 1000
    assert "Apache License" in (ROOT / "LICENSE").read_text()


def test_brand_images():
    """Square PNG images of the sizes Home Assistant asks for (icon 256, icon@2x 512)."""
    for name, size in (("icon.png", 256), ("icon@2x.png", 512), ("logo.png", 256), ("logo@2x.png", 512)):
        data = (PACKAGE / "brand" / name).read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n", name
        assert struct.unpack(">II", data[16:24]) == (size, size), name


def test_only_the_write_platforms_of_the_proven_settings_are_shipped():
    """Numbers and selects for the settings, texts for the program days, the set-clock button, the write switch
    and the action set_program; no date, time, climate or water heater."""
    shipped = {p.name for p in PACKAGE.iterdir()}
    assert {"number.py", "select.py", "switch.py", "text.py", "button.py", "services.yaml", "repairs.py", "writer.py",
            "writes.py", "programs.py", "clock.py", "guard.py"} <= shipped
    assert not shipped & {"date.py", "time.py", "climate.py", "water_heater.py"}
    assert {"manifest.json", "metadata.json", "translations", "brand", "quality_scale.yaml"} <= shipped
