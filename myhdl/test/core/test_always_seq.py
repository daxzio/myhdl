
from myhdl import Signal, always_seq, ResetSignal
from myhdl._always_seq import AlwaysSeqError, _error
from helpers import raises_kind


def test_clock():
    """ check the edge parameter """

    # should fail without a valid Signal
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=0, isasync=True)

    with raises_kind(AlwaysSeqError, _error.EdgeType):

        @always_seq(clock, reset=reset)
        def logic1():
            pass

    # should work with a valid Signal
    clock = Signal(bool(0))
    try:

        @always_seq(clock.posedge, reset=reset)
        def logic2():
            pass

    except:
        assert False


def test_reset():
    """ check the reset parameter """

    # should fail without a valid ResetSignal
    clock = Signal(bool(0))
    reset = Signal(bool(0))

    with raises_kind(AlwaysSeqError, _error.ResetType):

        @always_seq(clock.posedge, reset=reset)
        def synch():
            pass

    # should work with a valid Signal
    reset = ResetSignal(0, active=0, isasync=True)
    try:

        @always_seq(clock.posedge, reset=reset)
        def synch2():
            pass

    except:
        assert False
