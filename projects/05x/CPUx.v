`default_nettype none

module CPUx(
  output wire[15:0] outM,
  output wire[14:0] addressM,
  output wire writeM,
  output wire[14:0] pc,
  input wire clk,
  input wire[15:0] inM,
  input wire[15:0] inst,
  input wire reset);

  wire op, w, d4, ia, c1, c2, c3, c4, c5, c6, d1, d2, d3, j1, j2, j3;

  // convenience
  assign op = inst[15];

  // invert w and d4 so we can use them like the other flags
  assign w = ~inst[14];
  assign d4 = ~inst[13];
  assign ia = inst[12];
  assign {c1, c2, c3, c4, c5, c6} = inst[11:6];
  assign {d1, d2, d3} = inst[5:3];
  assign {j1, j2, j3} = inst[2:0];

  // writeM is asserted only if C-instruction and d3 is set.
  assign writeM = d3 & op;

  // decided what values ends up in the A register
  wire[15:0] a_in;
  wire[15:0] alu_out;
  Mux16 mux_op(.out(a_in),
               .sel(op),
               .a(inst),
               .b(alu_out));
  // A register, loads only if d1 is asserted or if op is 0
  wire[15:0] a_out;
  wire a_load = d1 | ~op;
  assign addressM = a_out[14:0];

  Register A(.out(a_out),
             .clk(clk),
             .load(a_load),
             .in(a_in));

  // decides whether we use the reg A or inM for ALU
  // operation
  wire[15:0] alu_y;
  Mux16 mux_ia(.out(alu_y),
               .sel(ia),
               .a(a_out),
               .b(inM));

  // D register, loads only if d2 is asserted and we are
  // executing a C instruction
  wire[15:0] d_out;
  wire d_load = d2 & op;
  Register D(.out(d_out),
             .clk(clk),
             .load(d_load),
             .in(alu_out));

  wire[15:0] w_out;
  // for backward compat d4 is consider set when it is 0
  wire w_load = d4 & op;
  Register W(.out(w_out),
             .clk(clk),
             .load(w_load),
             .in(alu_out));


  // decides whether we use the reg D or W for ALU
  // operation. When w is 0 we use W and when 1 we use D
  wire[15:0] alu_x;
  Mux16 mux_w(.out(alu_x),
              .sel(w),
              .a(d_out),
              .b(w_out));

  // connect c1-c6 to ALU configuration bits
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
