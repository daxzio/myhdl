"""Regression checks that the Icarus VPI path is unchanged."""

from pathlib import Path

import pytest

from backends import IcarusBackend, _find_myhdl_vpi
from designs import DESIGNS


def test_icarus_vpi_present():
    backend = IcarusBackend()
    if not backend.available():
        pytest.skip("iverilog cosim not available")
    vpi = _find_myhdl_vpi()
    assert vpi is not None
    assert vpi.name == "myhdl.vpi"


def test_icarus_does_not_use_manifest():
    backend = IcarusBackend()
    design = DESIGNS["inc"]
    assert backend.env(design, Path("/tmp/work")) == {}


def test_icarus_command_uses_vvp():
    backend = IcarusBackend()
    if not backend.available():
        pytest.skip("iverilog cosim not available")
    cmd = backend.command(DESIGNS["inc"], Path("/tmp/work"))
    assert cmd[:2] == ["vvp", "-m"]
    assert cmd[2].endswith("myhdl.vpi")
