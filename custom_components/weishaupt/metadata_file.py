"""Which metadata of the definitions the integration uses: a verified file beside Home Assistant's configuration,
or the copy bundled in the package. No Home Assistant dependency.

A release of the definitions that needs no change of code (messages or settings added, write conditions, ranges,
risk classes, labels) then needs only a reload of the config entry, not a new release of the integration.

Where: `<config>/weishaupt/`, holding `weishaupt-metadata-<version>.json` and the `sha256sums-<version>.txt` of the
same release, copied there by the user from the release page (this version fetches nothing). The folder is kept by
backups and by updates of the integration, which replace `custom_components/weishaupt/` only.

A file is used only when all of these hold, otherwise the bundled copy is used and the reason is reported:
- its sha256 equals the line for its name in the `sha256sums` of the same version (integrity, not authenticity);
- it parses, and its `schema` is the one this code reads (a newer schema needs a newer integration);
- its definitions version lies in the range this code accepts (the second number of a version changes when a name
  changes: entities could lose their identity) and is newer than the bundled copy;
- it builds a model, as the bundled copy does.
Among several valid files, the newest version wins.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .model import ACCEPTED_DEFINITIONS, METADATA_FILE, SCHEMA, Model

FOLDER = "weishaupt"
_NAME = re.compile(r"^weishaupt-metadata-(\d+\.\d+\.\d+)\.json$")


def version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def accepted(version: str, spec: str = ACCEPTED_DEFINITIONS) -> bool:
    """`spec` like `>=0.5.3, <0.6`."""
    value = version_tuple(version)
    for clause in spec.split(","):
        clause = clause.strip()
        op = clause[:2] if clause[:2] in (">=", "<=") else clause[:1]
        bound = version_tuple(clause[len(op):].strip())
        size = max(len(value), len(bound))
        a, b = value + (0,) * (size - len(value)), bound + (0,) * (size - len(bound))
        if not {">=": a >= b, "<=": a <= b, ">": a > b, "<": a < b}[op]:
            return False
    return True


@dataclass
class Choice:
    """The metadata in use, where it comes from, and the files that were not used with the reason."""

    model: Model
    source: str  # "bundled" or the file name
    refused: dict[str, str] = field(default_factory=dict)  # file name -> reason


def _check(path: Path, bundled_version: str) -> tuple[Model | None, str]:
    match = _NAME.match(path.name)
    if match is None:
        return None, "not a metadata file name"
    version = match[1]
    sums = path.with_name(f"sha256sums-{version}.txt")
    if not sums.is_file():
        return None, f"no {sums.name} beside it"
    data = path.read_bytes()
    expected = {line.split()[-1].lstrip("*"): line.split()[0]
                for line in sums.read_text(encoding="utf-8").splitlines() if len(line.split()) >= 2}
    if expected.get(path.name) != hashlib.sha256(data).hexdigest():
        return None, f"its sha256 is not the one of {sums.name}"
    try:
        content = json.loads(data)
    except ValueError:
        return None, "not JSON"
    if content.get("schema") != SCHEMA:
        return None, f"schema {content.get('schema')!r}: this version of the integration reads schema {SCHEMA}"
    inner = str(content.get("definitions", {}).get("version", ""))
    if inner != version:
        return None, f"it says definitions {inner}, its name {version}"
    if not accepted(version):
        return None, f"definitions {version} are outside the range this version accepts ({ACCEPTED_DEFINITIONS})"
    if version_tuple(version) <= version_tuple(bundled_version):
        return None, f"not newer than the bundled definitions {bundled_version}"
    try:
        return Model.from_dict(content), ""
    except (KeyError, TypeError, ValueError) as err:
        return None, f"its content does not build a model: {err}"


def choose(folder: Path, bundled: Path = METADATA_FILE) -> Choice:
    """The newest valid metadata file of `folder`, else the bundled copy."""
    base = Model.load(bundled)
    choice = Choice(base, "bundled")
    if not folder.is_dir():
        return choice
    found = sorted((p for p in folder.iterdir() if _NAME.match(p.name)),
                   key=lambda p: version_tuple(_NAME.match(p.name)[1]), reverse=True)
    for path in found:
        model, reason = _check(path, base.version)
        if model is None:
            choice.refused[path.name] = reason
        else:
            choice.model, choice.source = model, path.name
            break  # older files are not looked at
    return choice
