"""Constant-output cosimulation test (initial TO update)."""

import random
from random import randrange

from myhdl import Simulation, StopSimulation, Signal, delay, intbv, negedge, posedge

random.seed(2)

VALS = [randrange(2) for _ in range(1000)]


def clk_gen(clk):
    while True:
        yield delay(10)
        clk.next = not clk


def stimulus(clk):
    for _ in VALS:
        yield negedge(clk)
    raise StopSimulation


def check(q, clk):
    for _ in VALS:
        yield posedge(clk)
    assert q == 1


def bench(cosim):
    q, clk = [Signal(intbv(0)) for _ in range(2)]
    dut = cosim("const_1", q=q, clk=clk)
    return Simulation(dut, clk_gen(clk), stimulus(clk), check(q, clk))


def test_const_1_run(cosim):
    bench(cosim).run(quiet=1)


def test_const_1_suspend(cosim):
    sim = bench(cosim)
    while sim.run(duration=randrange(1, 5), quiet=1):
        pass
