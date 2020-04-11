`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module DMux4Way_tb;
  wire a;
  wire b;
  wire c;
  wire d;
  reg[1:0] sel;
  reg in;

  reg a_expected;
  reg b_expected;
  reg c_expected;
  reg d_expected;
  wire y;
  DMux4Way UUT (.out_a(a),
                .out_b(b),
                .out_c(c),
                .out_d(d),
                .in(in),
                .sel(sel));

  reg [6:0] testdata[0:7];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, DMux4Way_tb);

    $readmemb("DMux4Way_tb.data", testdata);
    for (idx = 0; idx < 8; idx = idx + 1) begin
      {in, sel, a_expected, b_expected, c_expected, d_expected} = testdata[idx];
      #10
      if (a !== a_expected ||
          b !== b_expected ||
          c !== c_expected ||
          d !== d_expected
         ) begin
        $display("FAILED for test data #%d: %b", idx, testdata[idx]);
      end
    end

    $finish;
  end
endmodule

