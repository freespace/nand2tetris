`default_nettype none

module DFF(
  output reg out,
  input wire clk,
  input wire in
);

  always @(posedge clk) begin
    out = in;
  end

endmodule

