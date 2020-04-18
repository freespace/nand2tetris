`default_nettype none

module RAM16K(
  output wire[15:0] out,
  input wire clk,
  input wire load,
  input wire[13:0] addr,
  input wire[15:0] in);

  reg on = 1;
  reg[3:0] writemask = 4'b1111;

  SB_SPRAM256KA ram(.DATAOUT(out),

                    .CLOCK(clk),
                    .WREN(load),

                    .ADDRESS(addr),
                    .DATAIN(in),

                    .MASKWREN(writemask),
                    .CHIPSELECT(on),
                    .STANDBY(~on),
                    .SLEEP(~on),
                    .POWEROFF(on));

endmodule

