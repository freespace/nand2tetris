`default_nettype none

module FullAdder(
  output wire sum,
  output wire carry,
  input wire a,
  input wire b,
  input wire carry_in);

    wire sum_0;
    wire carry_0;
    wire carry_1;

    HalfAdder ha0(sum_0, carry_0, a, b);
    HalfAdder ha1(sum, carry_1, sum_0, carry_in);
    Or or0(carry, carry_1, carry_0);
endmodule
