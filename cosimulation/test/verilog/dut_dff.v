module dut_dff;

   reg	d /*verilator public_flat_rw*/;
   reg 	clk /*verilator public_flat_rw*/;
   reg 	reset /*verilator public_flat_rw*/;
   wire q /*verilator public_flat_rw*/;

   initial begin
`ifndef VERILATOR
      $from_myhdl(d, clk, reset);
      $to_myhdl(q);
`endif
   end

   dff dut (.q(q), .d(d), .clk(clk), .reset(reset));

endmodule // inc
