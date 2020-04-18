`default_nettype none

module PC(
  output wire[15:0] out,
  input wire clk,
  input wire inc,
  input wire load,
  input wire reset,
  input wire[15:0] in);

  // instead of using the ALU lets just implement x+1 logic
  // here directly
  wire[15:0] not_x;
  wire[15:0] adder_out;
  wire[15:0] x_plus_1;

  // /x
  Not16 inv_x(not_x, out);

  // /x + 0xFFFF
  Add16 adder(adder_out,
              not_x,
              16'hFFFF);

  // /(/x + 0xFFFF) = x + 1
  Not16 inv_adder_out(x_plus_1, adder_out);

  // 2 values could go into the register:
  // (a) x+1 or (b) in depending on state
  // of load

  wire[15:0] reg_in;
  wire[2:0] loadresetinc = {load, reset, inc};

  Mux8Way16 mux_reg_in(reg_in,
                       loadresetinc,
                       out,           //load=0 reset=0 inc=0
                       x_plus_1,      //load=0 reset=0 inc=1
                       16'h0000,      //load=0 reset=1 inc=0
                       16'hxxxx,      //load=0 reset=1 inc=1 (invalid)
                       in,            //load=1 reset=0 inc=0
                       16'h0000,      //load=1 reset=0 inc=1 (invalid)
                       16'h0000,      //load=1 reset=1 inc=0 (invalid)
                       16'h0000);     //load=1 reset=1 inc=1 (invalid)

  Register pc_reg(out,
                  clk,
                  1'b1,
                  reg_in);

endmodule
