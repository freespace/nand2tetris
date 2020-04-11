`default_nettype none

module Demux (
  output wire out_a,
  output wire out_b,
  input wire in,
  input wire sel
);

  wire not_sel;

  not inv1(not_sel, sel);
  and and1(out_a, in, not_sel);
  and and1(out_b, in, sel);

endmodule

