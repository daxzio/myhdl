"""MyHDL reference models without a cosimulation/test counterpart."""

from myhdl import Signal, always, always_comb, instances, intbv


def passthrough(a, b, width):
    @always_comb
    def comb():
        b.next = a

    return instances()


def xz_probe(clk, x_sig, z_sig, z_wide):
    """Reference: drive known 0/1 only (no X/Z in pure MyHDL)."""

    @always(clk.posedge)
    def logic():
        x_sig.next = 0
        z_sig.next = 0
        z_wide.next = 0

    return instances()
