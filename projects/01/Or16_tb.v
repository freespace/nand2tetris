`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module Or16_tb;
  reg[15:0] a;
  reg[15:0] b;
  wire[15:0] out;
  reg[15:0] out_expected;

  Or16 UUT (.out(out), .a(a), .b(b));

  reg [47:0] testdata[0:15];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, Or16_tb);

    $readmemb("Or16_tb.data", testdata);
    for (idx = 0; idx < 8; idx = idx + 1) begin
      {a, b, out_expected} = testdata[idx];
      #10
      if (out != out_expected) begin
        $display("FAILED for test data %b_%b", a, out_expected);
      end
    end

    $finish;
  end
endmodule

