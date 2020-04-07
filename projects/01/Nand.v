`default_nettype none

module Nand (
  input wire a,
  input wire b,
  output wire y
);

  assign y = a ~& b;

endmodule
