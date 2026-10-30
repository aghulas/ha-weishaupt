"""Load the Home Assistant independent modules of the integration without importing Home Assistant."""
import importlib.util
import sys
import types
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "custom_components" / "weishaupt"
sys.modules.setdefault("weishaupt_core", types.ModuleType("weishaupt_core")).__path__ = [str(SRC)]
for name in ("protocol", "guard", "registers"):
    spec = importlib.util.spec_from_file_location(f"weishaupt_core.{name}", SRC / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
