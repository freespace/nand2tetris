`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module Mux8Way16_tb;
  reg[15:0] a;
  reg[15:0] b;
  reg[15:0] c;
  reg[15:0] d;
  reg[15:0] e;
  reg[15:0] f;
  reg[15:0] g;
  reg[15:0] h;
  reg[2:0] sel;
  wire[15:0] out;
  reg[15:0] out_expected;

  Mux8Way16 UUT (.out(out),
                 .a(a),
                 .b(b),
                 .c(c),
                 .d(d),
                 .e(e),
                 .f(f),
                 .g(g),
                 .h(h),
                 .sel(sel));

  reg [146:0] testdata[0:15];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, Mux8Way16_tb);

    $readmemb("Mux8Way16_tb.data", testdata);
    for (idx = 0; idx < 16; idx = idx + 1) begin
      {a, b, c, d, e, f, g, h, sel, out_expected} = testdata[idx];
      #10
      if (out != out_expected || out === 16'bx ) begin
        $display("FAILED for test data #%d: %b", idx, testdata[idx]);
      end
    end

    $finish;
  end
endmodule

