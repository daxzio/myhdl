"""Incrementer cosimulation tests."""

import random
from random import randrange

import pytest

from myhdl import Simulation, StopSimulation, Signal, delay, intbv, negedge, posedge

random.seed(2)

ACTIVE_LOW, INACTIVE_HIGH = 0, 1


def clock_gen(clock):
    while True:
        yield delay(10)
        clock.next = not clock


def stimulus(enable, clock, reset):
    reset.next = ACTIVE_LOW
    yield negedge(clock)
    reset.next = INACTIVE_HIGH
    for _ in range(1000):
        enable.next = min(1, randrange(5))
        yield negedge(clock)
    raise StopSimulation


def check(count, enable, clock, reset, n):
    expect = 0
    yield posedge(reset)
    assert count == expect
    while True:
        yield posedge(clock)
        if enable:
            expect = (expect + 1) % n
        yield delay(1)
        assert count == expect


def bench(cosim, n=253):
    count, enable, clock, reset = [Signal(intbv(0)) for _ in range(4)]
    dut = cosim("inc", params={"n": n}, count=count, enable=enable, clock=clock, reset=reset)
    return Simulation(dut, clock_gen(clock), stimulus(enable, clock, reset), check(count, enable, clock, reset, n=n))


def test_inc_run(cosim):
    bench(cosim).run(quiet=1)


def test_inc_suspend(cosim):
    sim = bench(cosim)
    while sim.run(duration=randrange(1, 6), quiet=1):
        pass
