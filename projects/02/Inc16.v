`default_nettype none

module Inc16(
  output wire[15:0] out,
  input wire[15:0] a);

  reg[15:0] one = 16'b0000_0000_0000_0001;

  Add16 add0(.sum(out), .a(a), .b(one));
endmodule
