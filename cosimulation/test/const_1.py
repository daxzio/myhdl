"""Pure-MyHDL reference for the const_1 cosim DUT."""

from myhdl import always, instances


def const_1(q, clk):
    """Drive q to 1 on every clock edge (matches Verilog wire q = 1)."""

    @always(clk.posedge)
    def logic():
        q.next = 1

    return instances()
