`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module Register_tb;
  reg[15:0] in = 0;
  reg clk = 1;
  reg load = 0;
  wire[15:0] out;
  reg[15:0] out_expected;

  Register UUT (.out(out), .clk(clk), .load(load), .in(in));

  reg [32:0] testdata[0:149];
  integer idx;

  always #5 clk = ~clk;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, Register_tb);

    $readmemb("Register_tb.data", testdata);

    for (idx = 0; idx < 150; idx = idx + 0) begin
      // at t
      {in, load, out_expected} = testdata[idx];
      // need this delay for signal to propagate
      #1
      // the second part of the conditional is required to detect
      // when out is undefined, a condition not caught by !=
      if (out != out_expected || out === 1'bx ) begin
        $display("FAILED for test data #%d: %b", idx, testdata[idx]);
        $display("Expected %b got %b", out_expected, out);
      end

      // t+1
      // wait for the positive edge
      #4
      idx = idx + 1;
      {in, load, out_expected} = testdata[idx];
      #1
      if (out != out_expected || out === 1'bx ) begin
        $display("FAILED for test data #%d: %b", idx, testdata[idx]);
      end

      // wait until just before the next edge
      #4
      idx = idx + 1;
    end

    $finish;
  end
endmodule

