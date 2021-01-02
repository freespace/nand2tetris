`default_nettype none

// width of each RAM unit in bits
`define RAM_DATA_WIDTH 16

// number of bits that can be used to address _all_ of RAM
`define RAM_ADDR_WIDTH 15

// number of bits that can be used to address data ram
`define DATA_RAM_ADDR_WIDTH 14

// size of the video ram in number of valid addresses
`define VIDEO_RAM_SIZE  24*24

// number of bits needed to store the value VIDEO_RAM_SIZE
`define VIDEO_RAM_ADDR_WIDTH 10

// VIDEO RAM is only required to be 2 bits
`define VIDEO_RAM_DATA_WIDTH 2

// address to which if 1 is written will cause video ram to be shifted out
`define VIDEO_REFRESH_ADDR 15'b111_1111_1111_1111

/**
video_ram is shifted out of video_out, 1 bit
per negative edge of video_clk. When all of video
ram has been shifted out (LSB first) video_sync
is asserted. The cycle repeast on the negative edge
of video_sync.
*/
module RAM(
  output wire[`RAM_DATA_WIDTH-1:0] out,
  output wire video_out,
  output wire video_sync,
  input wire clk,
  input wire video_clk,
  input wire load,
  input wire[`RAM_ADDR_WIDTH-1:0] addr,
  input wire[`RAM_DATA_WIDTH-1:0] in);

  wire[`RAM_DATA_WIDTH-1:0] data_ram_out;
  wire[`RAM_DATA_WIDTH-1:0] video_ram_out;

  // note that even though video_cnt is an address counter
  // b/c this is connected to .out its width must match RAM_DATA_WIDTH
  wire[`RAM_DATA_WIDTH-1:0] video_cnt_out;
  wire[1:0] out_sel;

  wire is_refresh;

  /*
    3 outputs are possible:
    out_sel=00: data_ram
    out_sel=01: video_ram
    out_sel=10: video_cnt
  */
  Mux4Way16 out_mux(
    .out(out),
    .a(data_ram_out),
    .b(video_ram_out),
    .c(video_cnt_out),
    .d(16'b0),
    .sel(out_sel));

  // when the MSB is not set data_ram is directly connected
  RAM16K data_ram(.out(data_ram_out),
                  .clk(clk),
                  .load(load & ~addr[`DATA_RAM_ADDR_WIDTH]),
                  .addr(addr[`DATA_RAM_ADDR_WIDTH-1:0]),
                  .in(in));

  // this will probably have to be built from individual logic units
  reg[`VIDEO_RAM_DATA_WIDTH-1:0] video_ram[0:`VIDEO_RAM_SIZE-1];

  // this is one bit larger than required b/c we use `VIDEO_RAM_SIZE as
  // a sentinel value
  reg[`VIDEO_RAM_ADDR_WIDTH-1:0] video_cnt = 0;
  reg video_out_reg = 0;


  always @(posedge clk) begin
    if (~is_refresh & load & addr[`DATA_RAM_ADDR_WIDTH]) begin
      video_ram[addr[`VIDEO_RAM_ADDR_WIDTH-1:0]] <= in[`VIDEO_RAM_DATA_WIDTH-1:0];
    end
  end

  // always be shifting out the video ram
  always @(negedge video_clk) begin
    // reset video cnt if a 1 is written to VIDEO_REFRESH_ADDR. This will cause video sync to go
    // high and for shiftout of videoram to occur on subsequent edges.
    if (load & is_refresh & in[0] == 1) begin
      video_cnt = 0;
    end else if (video_cnt != `VIDEO_RAM_SIZE) begin
      // we need this 2-step b/c we need the value _before_ video_cnt is updated
      video_out_reg = video_ram[video_cnt][0];
      video_cnt = video_cnt + 1;
    end
  end

  assign video_sync = video_cnt == `VIDEO_RAM_SIZE;
  assign video_out = video_out_reg;

  // note that this can fail if VIDEO_RAM_ADDR_WIDTH is >= RAM_ADDR_WIDTH-1
  assign video_cnt_out[`VIDEO_RAM_ADDR_WIDTH-1:0] = video_cnt;
  assign video_cnt_out[`RAM_DATA_WIDTH-1:`VIDEO_RAM_ADDR_WIDTH] = 0;

  assign out_sel[0] = (~is_refresh) & addr[`DATA_RAM_ADDR_WIDTH];
  assign out_sel[1] = is_refresh;

  assign video_ram_out[`VIDEO_RAM_DATA_WIDTH-1:0] = video_ram[addr[`VIDEO_RAM_ADDR_WIDTH-1:0]];
  assign video_ram_out[`RAM_DATA_WIDTH-1:`VIDEO_RAM_DATA_WIDTH] = 0;

  assign is_refresh = addr == `VIDEO_REFRESH_ADDR;
endmodule

