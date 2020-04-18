`default_nettype none

module Mux4Way16 (
  output wire[15:0] out,
  input wire[1:0] sel,
  input wire[15:0] a,
  input wire[15:0] b,
  input wire[15:0] c,
  input wire[15:0] d
);

  wire[15:0] mux_ab_out;
  wire[15:0] mux_cd_out;

  Mux16 mux_ab(mux_ab_out, a, b, sel[0]);
  Mux16 mux_cd(mux_cd_out, c, d, sel[0]);

  Mux16 mux_final(out, mux_ab_out, mux_cd_out, sel[1]);
endmodule

