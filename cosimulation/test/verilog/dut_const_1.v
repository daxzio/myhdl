module dut_const_1;

   reg 	clk;
   wire q;

   initial begin
`ifndef VERILATOR
      $from_myhdl(clk);
      $to_myhdl(q);
`endif
   end

   const_1 dut (.q(q), .clk(clk) );

endmodule // inc
