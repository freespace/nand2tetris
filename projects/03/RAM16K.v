`default_nettype none

module RAM16K(
  output wire[15:0] out,
  input wire clk,
  input wire load,
  input wire[13:0] addr,
  input wire[15:0] in);


  SB_SPRAM256KA ram(.DATAOUT(out),

                    .CLOCK(clk),
                    .WREN(load),

                    .ADDRESS(addr),
                    .DATAIN(in),

                    .MASKWREN(4'b1111),
                    .CHIPSELECT(1'b1),
                    .STANDBY(1'b0),
                    .SLEEP(1'b0),
                    .POWEROFF(1'b1));

endmodule

