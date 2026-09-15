"""D flip-flop cosimulation tests."""

from random import randrange

from myhdl import Simulation, StopSimulation, Signal, delay, intbv, negedge, posedge

from bench_common import ACTIVE_LOW, INACTIVE_HIGH, VALS


def clk_gen(clk):
    while True:
        yield delay(10)
        clk.next = not clk


def stimulus(d, clk, reset):
    reset.next = ACTIVE_LOW
    yield negedge(clk)
    reset.next = INACTIVE_HIGH
    for v in VALS:
        d.next = v
        yield negedge(clk)
    raise StopSimulation


def check(q, clk, reset):
    yield posedge(reset)
    v_z = 0
    first = 1
    for v in VALS:
        yield posedge(clk)
        if not first:
            assert q == v_z
        first = 0
        yield delay(3)
        assert q == v
        v_z = v


def bench(cosim):
    q, d, clk, reset = [Signal(intbv(0)) for _ in range(4)]
    dut = cosim("dff", q=q, d=d, clk=clk, reset=reset)
    return Simulation(dut, clk_gen(clk), stimulus(d, clk, reset), check(q, clk, reset))


def test_dff_run(cosim):
    bench(cosim).run(quiet=1)


def test_dff_suspend(cosim):
    sim = bench(cosim)
    while sim.run(duration=randrange(1, 5), quiet=1):
        pass
