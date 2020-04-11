`default_nettype none

module Demux4Way (
  output wire out_a,
  output wire out_b,
  output wire out_c,
  output wire out_d,
  input wire in,
  input wire[1:0] sel
);

  wire ab_in;
  wire cd_in;

  DMux dmux_abcd(ab_in, cd_in, in, sel[0]);

  DMux dmux_ab(out_a, out_b, ab_in, sel[1]);
  DMux dmux_cd(out_c, out_d, cd_in, sel[1]);

endmodule

