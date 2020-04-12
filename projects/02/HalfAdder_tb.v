`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module HalfAdder_tb;
  reg a;
  reg b;

  wire sum;
  wire carry;

  reg sum_expected;
  reg carry_expected;

  HalfAdder UUT (.sum(sum), .carry(carry), .a(a), .b(b));

  reg [3:0] testdata[0:3];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, HalfAdder_tb);

    $readmemb("HalfAdder_tb.data", testdata);
    for (idx = 0; idx < 4; idx = idx + 1) begin
      {a, b, sum_expected, carry_expected} = testdata[idx];
      #10
      if (sum_expected !== sum_expected ||
          carry_expected !== carry_expected) begin
        $display("FAILED for test data #%d: %b", idx, testdata[idx]);
      end
    end

    $finish;
  end
endmodule

