`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

// replace #XXX# with suitable values, e.g. 16, 20
`define DATAWIDTH 16

module PC_tb;
  reg[`DATAWIDTH-1:0] in;
  reg load = 0;
  reg reset = 0;
  reg inc = 0;
  reg clk = 0;

  // do NOT assign a value to out otherwise it will
  // be double driven
  wire[`DATAWIDTH-1:0] out;

  PC UUT (out,
          clk,
          inc,
          load,
          reset,
          in);

  // generate a clock
  always #5 clk = ~clk;
  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, PC_tb);

    // half cycle offset
    #5
    // reset should work
    reset = 1;
    #5
    reset = 0;
    inc = 1;

    #50
    if (out !== 5) begin
      $display("FAIL test 1 out=%d", out);
    end

    // when inc is 0 we should stop counting
    inc = 0;
    #20
    if (out !== 5) begin
      $display("FAIL test 2 out=%d", out);
    end

    // test reset again
    reset = 1;
    #5
    reset = 0;
    inc = 0;
    #5
    if (out !== 0) begin
      $display("FAIL test 3 out=%d", out);
    end

    // lets load an arbitary number in
    load = 1;
    in = 16'hFF00;
    #5
    load = 0;
    #5
    if (out !== in) begin
      $display("FAIL test 4 0x%x != 0x%x", out, in);
    end

    // we should be able to count from the loaded
    // number
    inc = 1;
    #50
    if (out !== 16'hFF05) begin
      $display("FAIL test 4 out = 0x%x", out);
    end

    $finish;
  end
endmodule

