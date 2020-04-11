`default_nettype none

module Or (
  output wire out,
  input wire a,
  input wire b
);

  wire not_a, not_b;

  nand(not_a, a, a);
  nand(not_b, b, b);
  nand(out, not_a, not_b);

endmodule

