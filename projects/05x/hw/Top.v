`default_nettype none

`define S_CLK         P1A7
`define S_DATA        P1A8
`define S_RESET       P1A9

`define ROM_SIZE 1024*4

module Top(
  input wire CLK,
  // shift out clock
  output wire `S_CLK,
  // shift out data
  output wire `S_DATA,
  // shift out data reset
  output wire `S_RESET,
  output wire LED1,
  output wire LEDR_N,
  output wire LEDG_N);

  parameter CLK_FREQ_HZ=12000000;
  parameter CPU_FREQ_HZ=100000;
  parameter VIDEO_FREQ_HZ=100000;

  parameter PROG="firmware.hack";

  reg[24:0] cpu_clkdiv = 0;
  wire cpu_clk;

  reg[24:0] vid_clkdiv = 0;
  wire vid_clk;


  // generate ALU and shift clocks based on CLK input
  always @(posedge CLK) begin
    if (cpu_clkdiv == CLK_FREQ_HZ/CPU_FREQ_HZ) begin
      cpu_clkdiv <= 0;
    end else begin
      cpu_clkdiv <= cpu_clkdiv + 1;
    end

    if (vid_clkdiv == CLK_FREQ_HZ/VIDEO_FREQ_HZ) begin
      vid_clkdiv <= 0;
    end else begin
      vid_clkdiv <= vid_clkdiv + 1;
    end

    inst <= ROM[pc];
  end

  assign cpu_clk = cpu_clkdiv < CLK_FREQ_HZ/(2*CPU_FREQ_HZ);
  assign vid_clk = vid_clkdiv < CLK_FREQ_HZ/(2*VIDEO_FREQ_HZ);

  reg[7:0] reset = 8'hFF;
  wire[14:0] pc;
  reg[15:0] inst;

  reg[15:0] ROM[0:`ROM_SIZE-1];
  // load the program to be executed
  initial begin
    $readmemb(PROG, ROM);
  end

  assign `S_CLK = vid_clk;
  assign LED1 = cpu_clk;
  assign LEDR_N = pc[0];
  assign LEDG_N = pc[1];

  always @(posedge cpu_clk) begin
    // generate a reset signal for 8 clocks. Once all the 1s
    // have been shifted out reset will be 0 and the PC will be
    // allowed to increment
    reset <= reset >> 1;
  end

  HACK hack(.pc(pc),
            .video_out(`S_DATA),
            .video_sync(`S_RESET),
            .clk(cpu_clk),
            .video_clk(vid_clk),
            .reset(reset[0]),
            .inst(inst));
endmodule
