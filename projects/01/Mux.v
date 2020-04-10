`default_nettype none

module Mux (
  output wire y,
  input wire a,
  input wire b,
  input wire sel
);

  wire not_sel, a_out, b_out;

  Not not1(not_sel, sel);
  and and1(a_out, not_sel, a);
  and and2(b_out, sel, b);
  or o1(y, a_out, b_out);

endmodule

