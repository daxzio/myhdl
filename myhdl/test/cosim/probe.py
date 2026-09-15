"""Behavioural capability probing for cosim backends."""

from __future__ import annotations

from pathlib import Path

from myhdl import Simulation, Signal, StopSimulation, delay, intbv

from backends import CosimBackend, IcarusBackend, PythonBackend, CapabilitySet
from designs import DESIGNS

# Non-zero so HDL 1'bx mapped to Signal._init is distinguishable from 2-state 0.
_X_INIT = 1


def probe_xz(backend: CosimBackend, workdir: Path) -> CapabilitySet:
    """Run xz_probe once and detect four_state / tristate support."""
    if isinstance(backend, PythonBackend) or not backend.available():
        return frozenset()

    design = DESIGNS["xz_probe"]
    workdir = workdir.resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    backend.build(design, workdir, {})

    clk = Signal(0)
    x_sig = Signal(_X_INIT)
    z_sig = Signal(0)
    z_wide = Signal(intbv(0)[16:])
    caps: set[str] = set()

    def run():
        yield delay(30)
        if z_sig == None or z_wide == None:
            caps.add("tristate")
        if int(x_sig) == _X_INIT:
            caps.add("four_state")
        raise StopSimulation

    dut = backend.create_dut(
        design,
        workdir,
        {},
        {
            "clk": clk,
            "x_sig": x_sig,
            "z_sig": z_sig,
            "z_wide": z_wide,
        },
    )
    Simulation(dut, run()).run(quiet=1)

    if isinstance(backend, IcarusBackend):
        caps.add("defparam")
    return frozenset(caps)
