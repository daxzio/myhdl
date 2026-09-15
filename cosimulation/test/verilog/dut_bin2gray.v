module dut_bin2gray;

   reg [`width-1:0] B;
   wire [`width-1:0] G;

   initial begin
`ifndef VERILATOR
      $from_myhdl(B);
      $to_myhdl(G);
`endif
   end

   bin2gray dut (.B(B), .G(G));
   defparam dut.width = `width;

endmodule
