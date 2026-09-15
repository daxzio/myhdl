module dut_const_1;

   reg 	clk /*verilator public_flat_rw*/;
   wire q /*verilator public_flat_rw*/;

   initial begin
`ifndef VERILATOR
      $from_myhdl(clk);
      $to_myhdl(q);
`endif
   end

   const_1 dut (.q(q), .clk(clk) );

endmodule // inc
