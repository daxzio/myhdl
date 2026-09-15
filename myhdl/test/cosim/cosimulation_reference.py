"""Import pure-MyHDL reference models used by PythonBackend."""

import importlib
import sys
from pathlib import Path

from models import passthrough, xz_probe

_REPO_ROOT = Path(__file__).resolve().parents[3]
_COSIM_TEST = _REPO_ROOT / "cosimulation" / "test"
if str(_COSIM_TEST) not in sys.path:
    sys.path.append(str(_COSIM_TEST))

_LOCAL_MODELS = {
    "passthrough": passthrough,
    "xz_probe": xz_probe,
}


def get_model(name: str):
    if name in _LOCAL_MODELS:
        return _LOCAL_MODELS[name]
    module = importlib.import_module(name)
    return getattr(module, name)
