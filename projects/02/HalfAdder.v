`default_nettype none

module HalfAdder (
  output wire sum,
  output wire carry,
  input wire a,
  input wire b
);

  Xor xor_sum(sum, a, b);
  And and_carry(carry, a, b);

endmodule

