`default_nettype none

module Xor (
  output wire out,
  input wire a,
  input wire b
);

  wire c, nand_ab;

  nand(nand_ab, a, b);
  Or or1(c, a, b);
  and(out, nand_ab, c);


endmodule

