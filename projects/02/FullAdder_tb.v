`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module FullAdder_tb;
  reg a;
  reg b;
  reg carry_in;

  wire sum;
  wire carry;

  reg sum_expected;
  reg carry_expected;

  FullAdder UUT (.sum(sum), 
                 .carry(carry), 
                 .a(a),
                 .b(b),
                 .carry_in(carry_in));

  reg [4:0] testdata[0:7];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, FullAdder_tb);

    $readmemb("FullAdder_tb.data", testdata);
    for (idx = 0; idx < 8; idx = idx + 1) begin
      {a, b, carry_in, sum_expected, carry_expected} = testdata[idx];
      #10
      if (sum_expected !== sum_expected ||
          carry_expected !== carry_expected) begin
        $display("FAILED for test data #%d: %b", idx, testdata[idx]);
      end
    end

    $finish;
  end
endmodule

