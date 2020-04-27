`default_nettype none

`define S_CLK         P1A7
`define S_DATA        P1A8
`define S_RESET       P1A9
`define CPU_FREQ_HZ   100

// must be at least 400x faster
// than ALU_FREQ_HZ
`define SHIFT_FREQ_HZ 40000

`define ROM_SIZE 1024*4
`define PROG "blink.hack"

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

  reg[24:0] cpu_clkdiv = 0;
  reg cpu_clk = 0;

  reg[24:0] s_clkdiv = 0;
  reg s_clk = 0;


  // generate ALU and shift clocks based on CLK input
  always @(posedge CLK) begin
    // best HACK's CPU runs at half the CPU_FREQ we scale
    // things accordingly here
    if (cpu_clkdiv == 12000000/(4*`CPU_FREQ_HZ)) begin
      cpu_clkdiv <= 0;
      cpu_clk <= ~cpu_clk;
    end else begin
      cpu_clkdiv <= cpu_clkdiv + 1;
    end

    if (s_clkdiv == 12000000/(2*`SHIFT_FREQ_HZ)) begin
      s_clkdiv <= 0;
      s_clk <= ~s_clk;
    end else begin
      s_clkdiv <= s_clkdiv + 1;
    end
  end

  reg[3:0] reset = 4'b1111;
  wire[14:0] pc;
  reg[15:0] inst;

  reg[15:0] ROM[0:`ROM_SIZE-1];
  // load the program to be executed
  initial begin
    $readmemb(`PROG, ROM);
  end
  // hopefully set it up as synchronous memory
  always @(negedge cpu_clk) begin
    inst = ROM[pc];
  end

  assign `S_CLK = s_clk;
  assign LED1 = cpu_clk;
  assign LEDR_N = pc[0];
  assign LEDG_N = pc[1];

  always @(posedge cpu_clk) begin
    // generate a reset signal for 4 clocks. Once all the 1s
    // have been shifted out reset will be 0 and the PC will be
    // allowed to increment
    reset <= reset >> 1;
  end

  HACK hack(.pc(pc),
            .video_out(`S_DATA),
            .video_sync(`S_RESET),
            .clk(cpu_clk),
            .video_clk(s_clk),
            .reset(reset[0]),
            .inst(inst));
endmodule
