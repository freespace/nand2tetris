`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module TEMPLATE_tb;
  reg[#WIDTH#:0] a;
  reg[#WIDTH#:0] b;
  // ...
  wire[#WIDTH#:0] out;
  reg[#WIDTH#:0] out_expected;

  TEMPLATE UUT (...);

  reg [#WIDTH#:0] testdata[0:#NROWS#];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, TEMPLATE_tb);

    $readmemb("TEMPLATE_tb.data", testdata);
    for (idx = 0; idx < #NROWS#; idx = idx + 1) begin
      {..., out_expected} = testdata[idx];
      #10
      // the second part of the conditional is required to detect
      // when out is undefined, a condition not caught by !=
      if (out != out_expected || out === #WIDTH#'bx ) begin
        $display("FAILED for test data #%d: %b", idx, testdata[idx]);
      end
    end

    $finish;
  end
endmodule

