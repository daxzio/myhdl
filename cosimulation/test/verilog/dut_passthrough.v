module dut_passthrough;

   reg [`width-1:0] a;
   wire [`width-1:0] b;

   initial begin
`ifndef VERILATOR
      $from_myhdl(a);
      $to_myhdl(b);
`endif
   end

   passthrough dut (.a(a), .b(b));
   defparam dut.width = `width;

endmodule
