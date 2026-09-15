"""Binary-to-Gray cosimulation tests."""

from myhdl import Simulation, Signal, delay, intbv, bin

MAX_WIDTH = 10


def next_ln(ln):
    ln0 = ["0" + codeword for codeword in ln]
    ln1 = ["1" + codeword for codeword in ln]
    ln1.reverse()
    return ln0 + ln1


def test_original_gray_code(cosim):
    ln = ["0", "1"]
    for width in range(2, MAX_WIDTH):
        ln = next_ln(ln)
        rn = []

        def stimulus(b, g, n):
            for i in range(2**n):
                b.next = intbv(i)
                yield delay(10)
                rn.append(bin(g, width=n))

        b = Signal(intbv(1))
        g = Signal(intbv(0))
        dut = cosim("bin2gray", params={"width": width}, B=b, G=g)
        sim = Simulation(dut, stimulus(b, g, width))
        sim.run(quiet=1)
        assert ln == rn


def test_single_bit_change(cosim):
    def test(b, g, g_z, width):
        b.next = intbv(0)
        yield delay(10)
        for i in range(1, 2**width):
            g_z.next = g
            b.next = intbv(i)
            yield delay(10)
            diffcode = bin(g ^ g_z)
            assert diffcode.count("1") == 1

    for width in range(2, MAX_WIDTH):
        b = Signal(intbv(1))
        g = Signal(intbv(0))
        g_z = Signal(intbv(0))
        dut = cosim("bin2gray", params={"width": width}, B=b, G=g)
        sim = Simulation(dut, test(b, g, g_z, width))
        sim.run(quiet=1)


def test_unique_code_words(cosim):
    def test(b, g, width):
        actual = []
        for i in range(2**width):
            b.next = intbv(i)
            yield delay(10)
            actual.append(int(g))
        actual.sort()
        expected = list(range(2**width))
        assert actual == expected

    for width in range(1, MAX_WIDTH):
        b = Signal(intbv(1))
        g = Signal(intbv(0))
        dut = cosim("bin2gray", params={"width": width}, B=b, G=g)
        sim = Simulation(dut, test(b, g, width))
        sim.run(quiet=1)
