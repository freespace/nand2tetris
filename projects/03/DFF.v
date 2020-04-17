`default_nettype none

module DFF(
  output wire out,
  input wire clk,
  input wire in
);

  SB_DFF dff(.Q(out),
             .C(clk),
             .D(in));

endmodule

