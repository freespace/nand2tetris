`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module Or8Way_tb;
  reg[7:0] a;
  wire out;
  reg out_expected;

  Or8Way UUT (.out(out), .a(a));

  reg [8:0] testdata[0:4];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, Or8Way_tb);

    $readmemb("Or8Way_tb.data", testdata);
    for (idx = 0; idx < 4; idx = idx + 1) begin
      {a, out_expected} = testdata[idx];
      #10
      if (out != out_expected) begin
        $display("FAILED for test data %b_%b", a, out_expected);
      end
    end

    $finish;
  end
endmodule

