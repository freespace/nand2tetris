`default_nettype none

module Xor (
  input wire a,
  input wire b,
  output wire y
);

  wire c, nand_ab;

  nand(nand_ab, a, b);
  Or or1(c, a, b);
  and(y, nand_ab, c);


endmodule

