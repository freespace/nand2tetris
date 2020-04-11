`default_nettype none

module And (
  output wire out,
  input wire a,
  input wire b
);

  wire c;
  nand(c, a, b);
  nand(out, c, c);
endmodule

