module xz_probe(clk, x_sig, z_sig, z_wide);

   input clk;
   output x_sig;
   output z_sig;
   output [15:0] z_wide;
   reg x_sig;
   reg z_sig;
   reg [15:0] z_wide;

   initial begin
      x_sig = 1'bx;
      z_sig = 1'bz;
      z_wide = 16'bz;
   end

endmodule
