`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module Inc16_tb;
  reg[15:0] a;
  wire[15:0] out;
  reg[15:0] out_expected;

  Inc16 UUT (.out(out), .a(a));

  reg [31:0] testdata[0:3];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, Inc16_tb);

    $readmemb("Inc16_tb.data", testdata);
    for (idx = 0; idx < 4; idx = idx + 1) begin
      {a, out_expected} = testdata[idx];
      #10
      // the second part of the conditional is required to detect
      // when out is undefined, a condition not caught by !=
      if (out != out_expected || out === 16'bx ) begin
        $display("FAILED for test data #%d: %b", idx, testdata[idx]);
      end
    end

    $finish;
  end
endmodule

