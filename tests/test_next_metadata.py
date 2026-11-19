"""Hook for a new definitions release: point WEISHAUPT_NEXT_METADATA at its `weishaupt-metadata-<v>.json` (with its
`sha256sums-<v>.txt` beside it) and run this file. It checks, without a release of the integration, that the file is
accepted beside the configuration and what it would bring: messages read without an entity name (they wait), types
the model does not know, writable settings. Skipped when the variable is not set (CI)."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from custom_components.weishaupt.metadata_file import choose
from custom_components.weishaupt.model import Model

NEXT = os.environ.get("WEISHAUPT_NEXT_METADATA")
pytestmark = pytest.mark.skipif(not NEXT, reason="WEISHAUPT_NEXT_METADATA not set")


def test_the_next_release_is_taken_and_complete(tmp_path):
    source = Path(NEXT)
    version = source.stem.removeprefix("weishaupt-metadata-")
    for name in (source.name, f"sha256sums-{version}.txt"):
        shutil.copyfile(source.parent / name, tmp_path / name)
    choice = choose(tmp_path)
    assert choice.source == source.name, choice.refused  # checksum, schema, version range, content
    model: Model = choice.model
    unnamed = [d.key for d in model.value_entities if not d.name.get("en")]
    assert unnamed == [], f"messages without an English label: {unnamed}"
    bundled = Model.load()
    added = sorted(set(model.messages) - set(bundled.messages))
    removed = sorted(set(bundled.messages) - set(model.messages))
    print(f"\n{version}: {len(model.messages)} messages, {len(added)} added, {len(removed)} removed; "
          f"{len(model.setting_entities)} settings entities; added: {added[:20]}")
    # a message removed or renamed without `renamed_from` would orphan entities: the second number must change
    renamed = {m.renamed_from for m in model.messages.values() if m.renamed_from}
    assert not [k for k in removed if k not in renamed] or version.split(".")[1] != bundled.version.split(".")[1]
