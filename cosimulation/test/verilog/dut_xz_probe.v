module dut_xz_probe;

   reg clk;
   wire x_sig;
   wire z_sig;
   wire [15:0] z_wide;

   initial begin
`ifndef VERILATOR
      $from_myhdl(clk);
      $to_myhdl(x_sig, z_sig, z_wide);
`endif
   end

   xz_probe dut (.clk(clk), .x_sig(x_sig), .z_sig(z_sig), .z_wide(z_wide));

endmodule
