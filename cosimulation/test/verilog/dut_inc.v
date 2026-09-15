module dut_inc;

   reg	enable /*verilator public_flat_rw*/;
   reg 	clock /*verilator public_flat_rw*/;
   reg 	reset /*verilator public_flat_rw*/;
   wire [15:0] count /*verilator public_flat_rw*/;

   initial begin
`ifndef VERILATOR
      $from_myhdl(enable, clock, reset);
      $to_myhdl(count);
`endif
   end

   inc dut (.count(count), .enable(enable), .clock(clock), .reset(reset));
   defparam dut.n= `n;

endmodule // inc
