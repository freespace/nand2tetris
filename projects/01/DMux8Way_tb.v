`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module DMux8Way_tb;
  wire a;
  wire b;
  wire c;
  wire d;
  wire e;
  wire f;
  wire g;
  wire h;
  reg[2:0] sel;
  reg in;

  reg a_expected;
  reg b_expected;
  reg c_expected;
  reg d_expected;
  reg e_expected;
  reg f_expected;
  reg g_expected;
  reg h_expected;
  DMux8Way UUT (.out_a(a),
                .out_b(b),
                .out_c(c),
                .out_d(d),
                .out_e(e),
                .out_f(f),
                .out_g(g),
                .out_h(h),
                .in(in),
                .sel(sel));

  reg [12:0] testdata[0:15];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, DMux8Way_tb);

    $readmemb("DMux8Way_tb.data", testdata);
    for (idx = 0; idx < 16; idx = idx + 1) begin
      {in,
       sel,
       a_expected,
       b_expected,
       c_expected,
       d_expected,
       e_expected,
       f_expected,
       g_expected,
       h_expected} = testdata[idx];
      #10
      if (a !== a_expected ||
          b !== b_expected ||
          c !== c_expected ||
          d !== d_expected ||
          e !== e_expected ||
          f !== f_expected ||
          g !== g_expected ||
          h !== h_expected
         ) begin
        $display("FAILED for test data #%d: %b", idx, testdata[idx]);
      end
    end

    $finish;
  end
endmodule

