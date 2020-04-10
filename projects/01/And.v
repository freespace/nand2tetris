`default_nettype none

module And (
  output wire y,
  input wire a,
  input wire b
);

  wire c;
  nand(c, a, b);
  nand(y, c, c);
endmodule

