`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module Not16_tb;
  reg[15:0] a;
  wire[15:0] out;
  reg[15:0] out_expected;

  Not16 UUT (.out(out), .a(a));

  reg [31:0] testdata[0:7];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, Not16_tb);

    $readmemb("Not16_tb.data", testdata);
    for (idx = 0; idx < 8; idx = idx + 1) begin
      {a, out_expected} = testdata[idx];
      #10
      if (out != out_expected) begin
        $display("FAILED for test data %b_%b", a, out_expected);
      end
    end

    $finish;
  end
endmodule

