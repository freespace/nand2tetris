`default_nettype none

module Bit(
  output wire out,
  input wire clk,
  input wire load,
  input wire in);

  wire mux_out;

  Mux mux_inout(.out(mux_out), .sel(load), .a(out), .b(in));
  DFF dff(.out(out), .clk(clk), .in(mux_out));

endmodule
