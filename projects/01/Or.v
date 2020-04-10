`default_nettype none

module Or (
  output wire y,
  input wire a,
  input wire b
);

  wire not_a, not_b;

  nand(not_a, a, a);
  nand(not_b, b, b);
  nand(y, not_a, not_b);

endmodule

