`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

`define NTESTROWS 5
`define PROG "test_2.hack"

module HACK_tb;
  reg clk = 0;
  reg reset;
  wire[14:0] pc;
  wire[15:0] inst;
  wire[15:0] ram_data;
  wire[14:0] ram_addr;

  reg[15:0] ROM[0:16383];

  HACK UUT (.ram_data(ram_data),
            .ram_addr(ram_addr),
            .pc(pc),
            .clk(clk),
            .reset(reset),
            .inst(inst));

  assign inst = ROM[pc];

  always #5 clk = ~clk;

  integer idx;
  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, HACK_tb);
    $readmemb(`PROG, ROM);

    // reset for 2 cycles
    reset = 1;
    #20
    reset = 0;

    #10000

    $finish;
  end
endmodule


