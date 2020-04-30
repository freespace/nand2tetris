`default_nettype none

`define VIDEO_RAM_SIZE  16*16
/**
video_ram is shifted out of video_out, 1 bit
per negative edge of video_clk. When all of video
ram has been shifted out (LSB first) video_sync
is asserted for 1 cycle of video_clk
*/
module RAM(
  output wire[15:0] out,
  output wire video_out,
  output wire video_sync,
  input wire clk,
  input wire video_clk,
  input wire load,
  input wire[14:0] addr,
  input wire[15:0] in);

  // when the MSB is not set data_ram is directly connected
  RAM16K data_ram(.out(out),
                  .clk(clk),
                  .load(load & ~addr[14]),
                  .addr(addr[13:0]),
                  .in(in));

  // this will probably have to be built from individual logic units
  reg video_ram[0:`VIDEO_RAM_SIZE-1];

  // this is one bit larger than required b/c we use `VIDEO_RAM_SIZE as
  // a sentinel value
  reg[8:0] video_cnt = 0;
  reg video_out_reg = 0;

  // only the LSB matters
  always @(posedge clk) begin
    if (load & addr[14]) begin
      video_ram[addr[7:0]] = in[0];
    end
  end

  // always be shifting out the video ram
  always @(negedge video_clk) begin
    if (video_cnt == `VIDEO_RAM_SIZE) begin
      video_cnt <= 0;
    end else begin
      video_out_reg = video_ram[video_cnt];
      video_cnt = video_cnt + 1;
    end
  end

  assign video_sync = video_cnt == `VIDEO_RAM_SIZE;
  assign video_out = video_out_reg;

endmodule

