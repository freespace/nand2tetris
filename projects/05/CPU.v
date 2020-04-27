`default_nettype none

/**
  The clk2x signal should be twice as fast as the intended speed of the CPU.
  Memory connected to this CPU should be clocked using clk2x. This is a a hack
  to work around the fact the HACK design expects async memory while we only
  have HW IP cores for sync memory.
*/
module CPU(
  output wire[15:0] outM,
  output wire[14:0] addressM,
  output wire writeM,
  output wire[14:0] pc,
  input wire clk2x,
  input wire[15:0] inM,
  input wire[15:0] inst,
  input wire reset);

  reg[1:0] clk_cnt = 0;
  wire clk;

  always @(posedge clk2x) begin
    clk_cnt <= clk_cnt + 1;
  end
  assign clk = clk_cnt[0];

  wire op, ia, c1, c2, c3, c4, c5, c6, d1, d2, d3, j1, j2, j3;

  // convenience
  assign op = inst[15];
  assign ia = inst[12];
  assign {c1, c2, c3, c4, c5, c6} = inst[11:6];
  assign {d1, d2, d3} = inst[5:3];
  assign {j1, j2, j3} = inst[2:0];

  // writeM is asserted only if C-instruction and d3 is set.
  // Additionally we need to make sure it is never set on
  // when clk2x is positive to ensure valid inMem when
  // clk is positive. Additionally we want to writeM to
  // only be asserted AFTER an instruction has been executed
  // which means when clk is positive.
  assign writeM = d3 & op & ~clk2x & clk;

  // decided what values ends up in the A register
  wire[15:0] a_in;
  wire[15:0] alu_out;
  Mux16 mux_op(.out(a_in),
               .sel(op),
               .a(inst),
               .b(alu_out));
  // A register, loads only if d1 is asserted or if op is 0
  wire[15:0] a_out;
  wire a_load;

  reg[14:0] addressM_buf;
  assign a_load = d1 | ~op;
  assign addressM = addressM_buf;

  always @(negedge clk) begin
    addressM_buf <= a_out[14:0];
  end

  Register A(.out(a_out),
             .clk(clk2x),
             .load(a_load),
             .in(a_in));

  // D register, loads only if d2 is asserted and we are
  // executing a C instruction
  wire[15:0] alu_x;
  wire d_load = d2 & op;
  Register D(.out(alu_x),
             .clk(clk2x),
             .load(d_load),
             .in(alu_out));

  // decides whether we use the reg A or inM for ALU
  // operation
  wire[15:0] alu_y;
  Mux16 mux_ia(.out(alu_y),
               .sel(ia),
               .a(a_out),
               .b(inM));

  // connect D to ALU.x and A/inM to ALU.y and c1-c6
  // to ALU configuration bits
  wire ng, zr;

  ALU alu(.out(alu_out),
          .zr(zr),
          .ng(ng),
          .x(alu_x),
          .y(alu_y),
          .zx(c1),
          .nx(c2),
          .zy(c3),
          .ny(c4),
          .f(c5),
          .no(c6));
  // alu_out is outM
  assign outM = alu_out;

  // compute the jump signals
  wire j_lt, j_gt, j_eq, pc_load;

  assign j_lt = ng & j1;
  assign j_eq = zr & j2;
  // ~ng is not enough b/c zr might be set
  assign j_gt = ~ng & ~zr & j3;
  // loading, aka jumping, is only valid for C instructions
  assign pc_load = (op & (j_lt | j_eq | j_gt)) & ~reset;

  // if any of the jump signals are set then we load the value in the A register
  // into the PC register
  wire[15:0] pc_out;
  wire pc_inc;
  assign pc = pc_out[14:0];
  // if we are not loading or resetting we are incrementing. We need
  // this b/c I implemented PC such that setting inc while reset or
  // load is also set is undefined behaviour
  assign pc_inc = ~reset & ~pc_load;
  PC prog_counter(.out(pc_out),
                  .clk(clk),
                  .inc(pc_inc),
                  .load(pc_load),
                  .reset(reset),
                  .in(a_out));

endmodule
