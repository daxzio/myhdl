module passthrough(a, b);

   parameter width = 8;
   input [width-1:0] a;
   output [width-1:0] b;

   assign b = a;

endmodule
