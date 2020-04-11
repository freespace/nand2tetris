`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module DMux_tb;
  wire a;
  wire b;
  reg sel;
  reg in;

  reg a_expected;
  reg b_expected;
  wire y;
  Demux UUT (.out_a(a), .out_b(b), .in(in), .sel(sel));

  reg [3:0] testdata[0:3];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, Demux_tb);

    $readmemb("Demux_tb.data", testdata);
    for (idx = 0; idx < 4; idx = idx + 1) begin
      {in, sel, a_expected, b_expected} = testdata[idx];
      #10
      if (a != a_expected || b != b_expected) begin
        $display("FAILED for test data %b_%b_%b_%b", in, sel, a_expected, b_expected);
      end
    end

    $finish;
  end
endmodule

