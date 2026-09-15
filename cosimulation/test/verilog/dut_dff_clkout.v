module dut_dff_clkout;

   wire clkout /*verilator public_flat_rw*/;
   reg	d /*verilator public_flat_rw*/;
   reg 	clk /*verilator public_flat_rw*/;
   reg 	reset /*verilator public_flat_rw*/;
   wire q /*verilator public_flat_rw*/;

   initial begin
`ifndef VERILATOR
      $from_myhdl(d, clk, reset);
      $to_myhdl(clkout, q);
`endif
   end

   dff_clkout dut (.clkout(clkout), .q(q), .d(d), .clk(clk), .reset(reset));
   
endmodule
