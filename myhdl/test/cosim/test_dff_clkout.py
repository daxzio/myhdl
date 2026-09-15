"""dff_clkout cosimulation tests."""

from random import randrange

from myhdl import Simulation, StopSimulation, Signal, delay, intbv, negedge, posedge

from bench_common import ACTIVE_LOW, INACTIVE_HIGH, VALS


def clk_gen(clk):
    while True:
        yield delay(10)
        clk.next = not clk


def stimulus(d, clkout, reset):
    reset.next = ACTIVE_LOW
    yield negedge(clkout)
    reset.next = INACTIVE_HIGH
    for v in VALS:
        d.next = v
        yield negedge(clkout)
    raise StopSimulation


def check(q, clkout, reset):
    yield posedge(reset)
    v_z = 0
    first = 1
    for v in VALS:
        yield posedge(clkout)
        if not first:
            assert q == v_z
        first = 0
        yield delay(3)
        assert q == v
        v_z = v


def bench(cosim):
    clkout = Signal(intbv(0))
    q = Signal(intbv(0), delay=1)
    d = Signal(intbv(0))
    clk = Signal(intbv(0))
    reset = Signal(intbv(0))
    dut = cosim("dff_clkout", clkout=clkout, q=q, d=d, clk=clk, reset=reset)
    return Simulation(dut, clk_gen(clk), stimulus(d, clkout, reset), check(q, clkout, reset))


def test_dff_clkout_run(cosim):
    bench(cosim).run(quiet=1)


def test_dff_clkout_suspend(cosim):
    sim = bench(cosim)
    while sim.run(duration=randrange(1, 5), quiet=1):
        pass
