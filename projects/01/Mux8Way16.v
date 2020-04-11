`default_nettype none

module Mux8Way16 (
  output wire[15:0] out,
  input wire[15:0] a,
  input wire[15:0] b,
  input wire[15:0] c,
  input wire[15:0] d,
  input wire[15:0] e,
  input wire[15:0] f,
  input wire[15:0] g,
  input wire[15:0] h,
  input wire[2:0] sel
);

  wire[15:0] mux_ab_out;
  wire[15:0] mux_cd_out;
  wire[15:0] mux_ef_out;
  wire[15:0] mux_gh_out;

  wire[15:0] mux_abcd_out;
  wire[15:0] mux_efgh_out;

  Mux16 mux_ab(mux_ab_out, a, b, sel[0]);
  Mux16 mux_cd(mux_cd_out, c, d, sel[0]);
  Mux16 mux_ef(mux_ef_out, e, f, sel[0]);
  Mux16 mux_gh(mux_gh_out, g, h, sel[0]);

  Mux16 mux_abcd(mux_abcd_out, mux_ab_out, mux_cd_out, sel[1]);
  Mux16 mux_efgh(mux_efgh_out, mux_ef_out, mux_gh_out, sel[1]);

  Mux16 mux_output(out, mux_abcd_out, mux_efgh_out, sel[2]);
endmodule

