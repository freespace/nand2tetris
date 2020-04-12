`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module Add16_tb;
  reg[15:0] a;
  reg[15:0] b;
  // ...
  wire[15:0] sum;
  reg[15:0] sum_expected;

  Add16 UUT (.sum(sum), .a(a), .b(b));

  reg [47:0] testdata[0:5];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, Add16_tb);

    $readmemb("Add16_tb.data", testdata);
    for (idx = 0; idx < 6; idx = idx + 1) begin
      {a, b, sum_expected} = testdata[idx];
      #10
      if (sum != sum_expected || sum == 16'bx ) begin
        $display("FAILED for test data #%d: %b", idx, testdata[idx]);
      end
    end

    $finish;
  end
endmodule

