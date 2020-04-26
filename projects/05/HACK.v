`default_nettype none

module HACK(
  output wire[15:0] ram_data,
  output wire[14:0] ram_addr,
  output wire[14:0] pc,
  input wire clk,
  input wire reset,
  input wire[15:0] inst);

  wire[15:0] inM;
  wire[15:0] outM;
  wire[14:0] addressM;
  wire writeM;

  assign ram_data = inM;
  assign ram_addr = addressM;

  RAM16K ram(.out(inM),
             .clk(clk),
             .load(writeM),
             .addr(addressM[13:0]),
             .in(outM));

  CPU cpu(.outM(outM),
          .addressM(addressM),
          .writeM(writeM),
          .pc(pc),
          .clk(clk),
          .inM(inM),
          .inst(inst),
          .reset(reset));
endmodule
