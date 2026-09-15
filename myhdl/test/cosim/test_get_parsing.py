"""Unit tests for Cosimulation._get hex parsing (no simulator required)."""

from myhdl import Signal, intbv
from myhdl._Cosimulation import Cosimulation


class _MockCosim(Cosimulation):
    """Cosimulation that skips subprocess; inject _get input via _rt."""

    def __init__(self, **kwargs):
        self._fromSignames = []
        self._fromSizes = []
        self._fromSigs = []
        self._toSignames = list(kwargs.keys())
        self._toSizes = [16 if k == "wide" else 1 for k in kwargs]
        self._toSigs = list(kwargs.values())
        self._toSigDict = dict(kwargs)
        self._hasChange = 0
        self._getMode = 1
        self._rt = None
        self._wf = None

    def feed(self, line: str):
        import os
        rt, wt = os.pipe()
        os.write(wt, line.encode())
        os.close(wt)
        self._rt = rt
        self._getMode = 1
        self._get()
        os.close(rt)
        for sig in self._toSigs:
            sig._update()


def test_get_all_z_multi_bit():
    wide = Signal(intbv(0)[16:])
    cosim = _MockCosim(wide=wide)
    cosim.feed("0 wide zzzz")
    assert wide == None


def test_get_all_x_multi_bit():
    wide = Signal(intbv(0xA5)[16:])
    wide.next = 0
    wide._update()
    cosim = _MockCosim(wide=wide)
    cosim.feed("0 wide xxxx")
    assert int(wide) == 0xA5


def test_get_mixed_xz_becomes_zero():
    """Partial x/z hex is not 4-state; int('1x0z', 16) fails and becomes intbv(0)."""
    wide = Signal(intbv(0xFFFF)[16:])
    wide.next = 0xFFFF
    wide._update()
    cosim = _MockCosim(wide=wide)
    cosim.feed("0 wide 1x0z")
    assert int(wide) == 0
