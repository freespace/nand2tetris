`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module Mux_tb;
  reg a;
  reg b;
  reg sel;
  reg y_expected;
  wire y;
  Mux UUT (.y(y), .a(a), .b(b), .sel(sel));

  reg [3:0] testdata[0:7];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, Mux_tb);

    $readmemb("Mux_tb.data", testdata);
    for (idx = 0; idx < 8; idx = idx + 1) begin
      {a, b, sel, y_expected} = testdata[idx];
      #10
      if (y != y_expected) begin
        $display("FAILED for test data %b_%b_%b_%b", a, b, sel, y_expected);
      end
    end

    $finish;
  end
endmodule

