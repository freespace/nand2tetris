`default_nettype

module ALU(
  output wire[15:0] out,

  output wire zr,
  output wire ng,

  input wire[15:0] x,
  input wire[15:0] y,

  input wire zx,
  input wire nx,
  input wire zy,
  input wire ny,
  input wire f,
  input wire no
);

  reg[15:0] zero = 16'b0;
  wire[15:0] x1, y1;

  // zero select
  Mux16 mux_zx(x1, x, zero, zx);
  Mux16 mux_zy(y1, y, zero, zy);

  // invert select
  wire[15:0] not_x1, not_y1;
  wire[15:0] x2, y2;

  Not16 inv_x1(not_x1, x1);
  Not16 inv_y1(not_y1, y1);

  Mux16 mux_nx(x2, x1, not_x1, nx);
  Mux16 mux_ny(y2, y1, not_y1, ny);

  // function select
  wire[15:0] out_sum, out_and;
  wire[15:0] out1;

  Add16 add_out(out_sum, x2, y2);
  And16 and_out(out_and, x2, y2);
  Mux16 mux_f(out1, out_and, out_sum, f);

  // output select
  wire[15:0] not_out1;

  Not16 inv_out1(not_out1, out1);
  Mux16 mux_no(out, out1, not_out1, no);

  // negative detect
  assign ng = out[15];

  // zero detect
  wire[7:0] out_h, out_l;
  wire not_zh, not_zl;
  wire not_zr;

  assign out_l = out[7:0];
  assign out_h = out[15:8];

  Or8Way or_out_h(not_zh, out_h);
  Or8Way or_out_l(not_zl, out_l);
  Or     or_not_zh(not_zr, not_zh, not_zl);
  Not    inv_zr(zr, not_zr);


endmodule


