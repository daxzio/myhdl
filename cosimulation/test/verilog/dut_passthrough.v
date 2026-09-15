module dut_passthrough;

   reg [`width-1:0] a /*verilator public_flat_rw*/;
   wire [`width-1:0] b /*verilator public_flat_rw*/;

   initial begin
`ifndef VERILATOR
      $from_myhdl(a);
      $to_myhdl(b);
`endif
   end

   passthrough dut (.a(a), .b(b));
   defparam dut.width = `width;

endmodule
