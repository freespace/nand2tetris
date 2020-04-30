`default_nettype none

module HACK(
  output wire[14:0] pc,
  output wire video_out,
  output wire video_sync,
  input wire clk,
  input wire video_clk,
  input wire reset,
  input wire[15:0] inst);

  wire[15:0] inM;
  wire[15:0] outM;
  wire[14:0] addressM;
  wire writeM;

  RAM ram(.out(inM),
          .video_out(video_out),
          .video_sync(video_sync),
          .clk(~clk),
          .video_clk(~video_clk),
          .load(writeM),
          .addr(addressM[14:0]),
          .in(outM));

  CPUx  cpu(.outM(outM),
            .addressM(addressM),
            .writeM(writeM),
            .pc(pc),
            .clk(clk),
            .inM(inM),
            .inst(inst),
            .reset(reset));
endmodule
