module dut_xz_probe;

   reg clk /*verilator public_flat_rw*/;
   wire x_sig /*verilator public_flat_rw*/;
   wire z_sig /*verilator public_flat_rw*/;
   wire [15:0] z_wide /*verilator public_flat_rw*/;

   initial begin
`ifndef VERILATOR
      $from_myhdl(clk);
      $to_myhdl(x_sig, z_sig, z_wide);
`endif
   end

   xz_probe dut (.clk(clk), .x_sig(x_sig), .z_sig(z_sig), .z_wide(z_wide));

endmodule
