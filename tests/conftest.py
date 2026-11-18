"""Test set-up.

Run the suite with `scripts/test.sh`, which creates the environment of `requirements_test.txt`.

The modules without Home Assistant dependency (`ebusd`, `model`, `guard`, `writes`) are loaded on their own as
`weishaupt_core.*`. With a bare pytest (no Home Assistant test plugin) the tests of `test_ha_*.py` are not
collected and the asynchronous tests are skipped with a message, instead of failing.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "custom_components" / "weishaupt"
DATA = Path(__file__).resolve().parent / "data"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

sys.modules.setdefault("weishaupt_core", types.ModuleType("weishaupt_core")).__path__ = [str(SRC)]
for name in ("ebusd", "model", "guard", "writes"):
    spec = importlib.util.spec_from_file_location(f"weishaupt_core.{name}", SRC / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

try:
    import pytest_homeassistant_custom_component  # noqa: F401
    HAVE_HA = True
except ImportError:
    HAVE_HA = False
    collect_ignore_glob = ["test_ha_*.py"]

from fake_ebusd import FakeEbusd  # noqa: E402


@pytest.fixture(scope="session")
def golden() -> dict:
    """Answers of a real ebusd (fork build 26.1) that loaded release 0.5.4, recorded without a bus."""
    return json.loads((DATA / "ebusd-golden.json").read_text(encoding="utf-8"))


@pytest.fixture
async def fake(golden, socket_enabled):
    server = FakeEbusd(golden)
    await server.start()
    yield server
    await server.stop()


if HAVE_HA:
    @pytest.fixture(autouse=True)
    def _custom_integrations(enable_custom_integrations):
        yield

    @pytest.fixture
    def entity_registry_enabled_by_default():
        """Create every entity enabled, for the tests about entities that are disabled when created."""
        from unittest.mock import PropertyMock, patch
        with patch("homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
                   new_callable=PropertyMock, return_value=True):
            yield
else:
    import inspect

    @pytest.fixture
    def socket_enabled():
        yield

    def pytest_collection_modifyitems(items):
        skip = pytest.mark.skip(reason="needs the test environment: run scripts/test.sh")
        for item in items:
            if inspect.iscoroutinefunction(getattr(item, "function", None)) or "fake" in item.fixturenames:
                item.add_marker(skip)
