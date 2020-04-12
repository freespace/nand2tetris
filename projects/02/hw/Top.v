`default_nettype none

`define S_CLK         P1A7
`define S_DATA        P1A8
`define S_RESET       P1A9
`define ALU_FREQ_HZ   100

// must be at least 56x faster
// than ALU_FREQ_HZ
`define SHIFT_FREQ_HZ 10000

// alu_state is x, y, out, zx, nx, zy, ny, f, no, ng, zr
// = 16 * 3 + 8 = 56 bits
`define ALU_STATE_SIZE 56

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

  reg[15:0] out;
  reg ng, zr;

  reg[`ALU_STATE_SIZE-1:0] alu_state = 0;

  reg[24:0] alu_clkdiv = 0;
  reg alu_clk = 0;

  reg[15:0] x = 0;
  reg[15:0] y = 0;

  reg zx = 0;
  reg nx = 1;
  reg zy = 1;
  reg ny = 1;
  reg f  = 1;
  reg no = 1;

  // we need a faster shift out clock than the ALU
  // clock b/c we want to shift out the entirety
  // of ALU state before the ALU updates itself
  reg[24:0] s_clkdiv = 0;
  reg s_clk = 0;

  // keeps track of how many bits we have shifted out
  reg[5:0] s_cnt = 0;

  assign `S_CLK = s_clk;
  assign `S_DATA = alu_state[0];
  assign `S_RESET = s_cnt == `ALU_STATE_SIZE;

  assign LED1 = alu_clk;
  assign LEDR_N = ~ng;
  assign LEDG_N = ~zr;

  ALU alu(.out(out),
          .zr(zr),
          .ng(ng),

          .x(x),
          .y(y),

          .zx(zx),
          .nx(nx),
          .zy(zy),
          .ny(ny),
          .f(f),
          .no(no));

  // generate ALU and shift clocks based on CLK input
  always @(posedge CLK) begin
    if (alu_clkdiv == 12000000/(2*`ALU_FREQ_HZ)) begin
      alu_clkdiv <= 0;
      alu_clk <= ~alu_clk;
    end else begin
      alu_clkdiv <= alu_clkdiv + 1;
    end

    if (s_clkdiv == 12000000/(2*`SHIFT_FREQ_HZ)) begin
      s_clkdiv <= 0;
      s_clk <= ~s_clk;
    end else begin
      s_clkdiv <= s_clkdiv + 1;
    end
  end

  always @(negedge s_clk) begin
    if (s_cnt == `ALU_STATE_SIZE) begin
      s_cnt <= 0;
      // alu_state is x, y, out, zx, nx, zy, ny, f, no, ng, zr
      alu_state <= {x, y, out, zx, nx, zy, ny, f, no, ng, zr};
    end else begin
      s_cnt <= s_cnt +1;
      alu_state <= alu_state >>1;
    end
  end

  always @(posedge alu_clk) begin
    if (out != 16'hFFFF) begin
      x <= out;
    end
  end

endmodule
