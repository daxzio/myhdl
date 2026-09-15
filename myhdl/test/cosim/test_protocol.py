"""Pipe-protocol and width-fidelity cosimulation tests."""

import pytest

from myhdl import CosimulationError, Simulation, Signal, StopSimulation, delay, intbv, now

from designs import DESIGNS

pytestmark = pytest.mark.usefixtures("backend")

_X_INIT = 1


def test_passthrough_widths(cosim):
    for width in (1, 8, 16, 33, 64, 100):
        a = Signal(intbv(0)[width:])
        b = Signal(intbv(0)[width:])

        def drive():
            for val in (0, (1 << width) - 1, (1 << (width - 1)) if width > 1 else 1):
                a.next = intbv(val)[width:]
                yield delay(20)
                assert b == a
            raise StopSimulation

        dut = cosim("passthrough", params={"width": width}, a=a, b=b)
        Simulation(dut, drive()).run(quiet=1)


def test_signed_round_trip(cosim):
    width = 16
    a = Signal(intbv(0, min=-(2**15), max=2**15 - 1))
    b = Signal(intbv(0, min=-(2**15), max=2**15 - 1))

    def drive():
        for val in (-1, -32768, 32766, 0, 42):
            a.next = val
            yield delay(20)
            assert b == val
        raise StopSimulation

    dut = cosim("passthrough", params={"width": width}, a=a, b=b)
    Simulation(dut, drive()).run(quiet=1)


def test_time_stays_in_step(cosim):
    a = Signal(intbv(0)[8:])
    b = Signal(intbv(0)[8:])

    def drive():
        a.next = 1
        yield delay(20)
        assert now() == 20
        a.next = 2
        yield delay(1)
        assert now() == 21
        yield delay(1000)
        assert now() == 1021
        raise StopSimulation

    dut = cosim("passthrough", params={"width": 8}, a=a, b=b)
    Simulation(dut, drive()).run(quiet=1)


def test_stop_reaps_child(backend, cosim):
    if backend.name == "python":
        pytest.skip("no child process on the Python backend")
    a = Signal(intbv(0)[8:])
    b = Signal(intbv(0)[8:])

    def drive():
        a.next = 1
        yield delay(20)
        raise StopSimulation

    dut = cosim("passthrough", params={"width": 8}, a=a, b=b)
    Simulation(dut, drive()).run(quiet=1)
    assert dut._child.poll() is not None


def _xz_probe_signals():
    clk = Signal(0)
    x_sig = Signal(_X_INIT)
    z_sig = Signal(0)
    z_wide = Signal(intbv(0)[16:])
    return clk, x_sig, z_sig, z_wide


@pytest.mark.requires("four_state")
def test_x_single_bit(cosim):
    clk, x_sig, z_sig, z_wide = _xz_probe_signals()

    def run():
        yield delay(30)
        # HDL 1'bx is mapped to Signal._init; _X_INIT is 1 so this is not tautological.
        assert int(x_sig) == _X_INIT
        raise StopSimulation

    dut = cosim(
        "xz_probe", clk=clk, x_sig=x_sig, z_sig=z_sig, z_wide=z_wide
    )
    Simulation(dut, run()).run(quiet=1)


@pytest.mark.requires("tristate")
def test_z_single_bit(cosim):
    clk, x_sig, z_sig, z_wide = _xz_probe_signals()

    def run():
        clk.next = 0
        yield delay(10)
        clk.next = 1
        yield delay(10)
        assert z_sig == None
        raise StopSimulation

    dut = cosim(
        "xz_probe", clk=clk, x_sig=x_sig, z_sig=z_sig, z_wide=z_wide
    )
    Simulation(dut, run()).run(quiet=1)


@pytest.mark.requires("tristate")
def test_z_multi_bit_from_hdl(cosim):
    """Multi-bit high-impedance values from HDL (hex 'zzzz...')."""
    clk, x_sig, z_sig, z_wide = _xz_probe_signals()

    def run():
        yield delay(30)
        assert z_wide == None
        raise StopSimulation

    dut = cosim(
        "xz_probe", clk=clk, x_sig=x_sig, z_sig=z_sig, z_wide=z_wide
    )
    Simulation(dut, run()).run(quiet=1)


def test_handshake_unknown_signal(backend, build_cache):
    if backend.name == "python":
        pytest.skip("handshake error test needs HDL cosim backend")

    design = DESIGNS["inc"]
    workdir = build_cache(backend, design, {"n": 8})
    count, enable, clock, reset = [Signal(intbv(0)) for _ in range(4)]
    with pytest.raises(CosimulationError):
        backend.create_dut(
            design,
            workdir,
            {"n": 8},
            {"count": count, "enable": enable, "clock": clock, "typo": reset},
        )
