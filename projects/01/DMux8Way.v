`default_nettype none

module DMux8Way (
  output wire out_a,
  output wire out_b,
  output wire out_c,
  output wire out_d,
  output wire out_e,
  output wire out_f,
  output wire out_g,
  output wire out_h,
  input wire in,
  input wire[2:0] sel
);

  wire abcd_in;
  wire efgh_in;

  DMux dmux_abcdefgh(abcd_in, efgh_in, in, sel[2]);
  DMux4Way dmux_abcd(out_a, out_b, out_c, out_d, abcd_in, sel[1:0]);
  DMux4Way dmux_efgh(out_e, out_f, out_g, out_h, efgh_in, sel[1:0]);

endmodule

