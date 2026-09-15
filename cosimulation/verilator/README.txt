MyHDL Verilator cosimulation
============================

Verilator has no $from_myhdl / $to_myhdl (vpi_register_systf is unimplemented).
This shim uses MYHDL_MANIFEST + vpi_handle_by_name instead.

Build one DUT:
  make -C cosimulation/verilator \
    WORKDIR=/tmp/vlt_inc DUT=dut_inc \
    SOURCES="cosimulation/test/verilog/inc.v cosimulation/test/verilog/dut_inc.v" \
    DEFS="n=253"

Run tests:
  make cosim_verilator          # shared cosim suite (Verilator only)
  make cosim_iverilog           # shared cosim suite (Icarus)
  make cosim                    # both
  make verilator_toverilog      # legacy toVerilog cosim (MYHDL_COSIM=verilator)

Requires Verilator 5.048+ (--timing enabled in the cosim Makefile).

Shared DUT wrappers and generated testbenches wrap $from_myhdl/$to_myhdl in
`ifndef VERILATOR so the same Verilog builds on Icarus and Verilator.
See myhdl/test/cosim/ for the backend-agnostic test suite.
