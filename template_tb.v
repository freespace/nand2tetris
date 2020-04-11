`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module TEMPLATE_tb;
  reg[#:0] a;
  reg[#:0] b;
  // ...
  wire[#:0] out;
  reg[#:0] out_expected;

  TEMPLATE UUT (...);

  reg [#:0] testdata[0:#];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, TEMPLATE_tb);

    $readmemb("TEMPLATE_tb.data", testdata);
    for (idx = 0; idx < #; idx = idx + 1) begin
      {..., out_expected} = testdata[idx];
      #10
      if (out != out_expected || out === #'bx ) begin
        $display("FAILED for test data #%d: %b", idx, testdata[idx]);
      end
    end

    $finish;
  end
endmodule

