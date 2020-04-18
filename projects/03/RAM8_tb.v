`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module RAM8_tb;
  reg[15:0] in = 0;
  reg[2:0] addr = 0;
  reg clk = 0;
  reg load = 0;
  wire[15:0] out;
  reg[15:0] out_expected;

  RAM8 UUT (.out(out), .clk(clk), .load(load), .addr(addr), .in(in));

  reg [35:0] testdata[0:149];
  integer idx;

  always #5 clk = ~clk;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, RAM8_tb);

    // the test provided by course is too hard to convert to verilog
    // so we are writing our own

    // test loading into a addr
    addr = 5;
    in = 16'h1234;
    load = 1;
    #10

    if (out !== in) begin
      $display("FAILED test 1");
    end

    // test loading into another addr
    addr = 0;
    in = 16'hABCD;
    load = 1;
    #10

    if (out !== in) begin
      $display("FAILED test 2");
    end

    // changing input without load=0 has no effect
    in = 16'h9876;
    load = 0;
    #10

    if (out === in) begin
      $display("FAILED test 3");
    end

    // changing to another addr changes to an old
    // value. in should be ignored
    addr = 5;
    load = 0;
    #10

    if (out !== 16'h1234) begin
      $display("FAILED test 4");
    end

    $finish;
  end
endmodule

