"""The metadata file beside the configuration: which one is used, and why a file is not."""
import copy
import hashlib
import json

import pytest

from weishaupt_core.metadata_file import accepted, choose
from weishaupt_core.model import METADATA_FILE

BUNDLED = json.loads(METADATA_FILE.read_text(encoding="utf-8"))


def release(folder, version: str, change=None, schema=None, sums: str | None = None, name: str | None = None):
    """Write `weishaupt-metadata-<version>.json` and its `sha256sums-<version>.txt`, as a release has them."""
    folder.mkdir(exist_ok=True)
    data = copy.deepcopy(BUNDLED)
    data["definitions"]["version"] = version
    if schema is not None:
        data["schema"] = schema
    if change:
        change(data)
    text = json.dumps(data).encode()
    file = folder / (name or f"weishaupt-metadata-{version}.json")
    file.write_bytes(text)
    digest = sums or hashlib.sha256(text).hexdigest()
    (folder / f"sha256sums-{version}.txt").write_text(f"{digest}  {file.name}\n")
    return file


def test_without_a_folder_the_bundled_copy(tmp_path):
    choice = choose(tmp_path / "weishaupt")
    assert choice.source == "bundled" and choice.model.version == BUNDLED["definitions"]["version"]


def test_a_newer_verified_file_is_used(tmp_path):
    folder = tmp_path / "weishaupt"
    release(folder, "1.4.2")
    choice = choose(folder)
    assert (choice.source, choice.model.version, choice.refused) == ("weishaupt-metadata-1.4.2.json", "1.4.2", {})


def test_a_bad_checksum_is_refused(tmp_path):
    folder = tmp_path / "weishaupt"
    release(folder, "1.4.2", sums="0" * 64)
    choice = choose(folder)
    assert choice.source == "bundled" and "sha256" in choice.refused["weishaupt-metadata-1.4.2.json"]


def test_no_sums_file_is_refused(tmp_path):
    folder = tmp_path / "weishaupt"
    release(folder, "1.4.2")
    (folder / "sha256sums-1.4.2.txt").unlink()
    assert "sha256sums-1.4.2.txt" in choose(folder).refused["weishaupt-metadata-1.4.2.json"]


def test_a_newer_schema_is_refused(tmp_path):
    folder = tmp_path / "weishaupt"
    release(folder, "1.4.2", schema=2)
    choice = choose(folder)
    assert choice.source == "bundled" and "schema 2" in choice.refused["weishaupt-metadata-1.4.2.json"]


@pytest.mark.parametrize("version,why", [("2.0.0", "outside the range"), ("0.5.15", "outside the range"),
                                         ("1.4.1", "not newer")])
def test_a_version_out_of_range_or_not_newer_is_refused(tmp_path, version, why):
    folder = tmp_path / "weishaupt"
    release(folder, version)
    choice = choose(folder)
    assert choice.source == "bundled" and why in choice.refused[f"weishaupt-metadata-{version}.json"]


def test_a_file_whose_name_and_content_disagree_is_refused(tmp_path):
    folder = tmp_path / "weishaupt"
    release(folder, "1.4.2", change=lambda d: d["definitions"].update(version="0.5.10"))
    assert "it says definitions 0.5.10" in choose(folder).refused["weishaupt-metadata-1.4.2.json"]


def test_a_content_that_builds_no_model_is_refused(tmp_path):
    folder = tmp_path / "weishaupt"
    release(folder, "1.4.2", change=lambda d: d.pop("devices"))
    assert "does not build a model" in choose(folder).refused["weishaupt-metadata-1.4.2.json"]


def test_the_newest_valid_file_wins(tmp_path):
    folder = tmp_path / "weishaupt"
    release(folder, "1.4.2")
    release(folder, "1.4.3", sums="1" * 64)
    release(folder, "1.4.4", schema=3)
    choice = choose(folder)
    assert choice.model.version == "1.4.2"
    assert set(choice.refused) == {"weishaupt-metadata-1.4.3.json", "weishaupt-metadata-1.4.4.json"}


def test_accepted():
    assert accepted("0.6.0") and accepted("0.7.0") and accepted("1.3.0") and not accepted("0.5.15") and not accepted("2.0.0")
