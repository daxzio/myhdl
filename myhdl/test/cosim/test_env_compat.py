"""Cosimulation(_env=...) forwards the environment to the child."""

import os
import sys

import pytest

from myhdl import Cosimulation, CosimulationError, Signal


def test_cosimulation_without_env_kwarg():
    with pytest.raises(CosimulationError):
        Cosimulation("/nonexistent/binary", dummy=0)


def test_cosimulation_forwards_env(tmp_path):
    marker = tmp_path / "seen"
    script = tmp_path / "echo_env.py"
    script.write_text(
        "import os, pathlib\n"
        "pathlib.Path(os.environ['MARKER']).write_text("
        "os.environ.get('MYHDL_PROBE', 'missing'))\n"
    )
    env = os.environ.copy()
    env["MARKER"] = str(marker)
    env["MYHDL_PROBE"] = "ok"
    with pytest.raises(CosimulationError):
        Cosimulation(
            [sys.executable, str(script)],
            _env=env,
            dummy=Signal(0),
        )
    assert marker.read_text() == "ok"


def test_signal_named_env_is_not_swallowed():
    with pytest.raises(CosimulationError):
        Cosimulation("/nonexistent/binary", env=Signal(0))
