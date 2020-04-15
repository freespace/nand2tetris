`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module DFF_tb;
  reg in = 0;
  reg clk = 0;
  wire out;

  DFF UUT (.out(out), .clk(clk), .in(in));

  always #5 clk = ~clk;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, DFF_tb);
    in = 0;
    #10
    if (out !== 0) begin
      $display("FAIL: Test 1");
    end

    in = 1;
    #10
    if (out !== 1) begin
      $display("FAIL: Test 2");
    end

    in = 0;
    #5
    if (out !== 1) begin
      $display("FAIL: Test 3");
    end
    #5
    if (out !== 0) begin
      $display("FAIL: Test 4");
    end

    in = 1;
    #5
    if (out !== 0) begin
      $display("FAIL: Test 5");
    end
    #5
    if (out !== 1) begin
      $display("FAIL: Test 6");
    end
    $finish;
  end
endmodule

