`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module Mux4Way16_tb;
  reg[15:0] a;
  reg[15:0] b;
  reg[15:0] c;
  reg[15:0] d;
  reg[1:0] sel;
  wire[15:0] out;
  reg[15:0] out_expected;

  Mux4Way16 UUT (.out(out), .a(a), .b(b), .c(c), .d(d), .sel(sel));

  reg [81:0] testdata[0:7];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, Mux4Way16_tb);

    $readmemb("Mux4Way16_tb.data", testdata);
    for (idx = 0; idx < 8; idx = idx + 1) begin
      {a, b, c, d, sel, out_expected} = testdata[idx];
      #10
      if (out != out_expected || out === 16'bx ) begin
        $display("FAILED for test data #%d: %b", idx, testdata[idx]);
      end
    end

    $finish;
  end
endmodule

