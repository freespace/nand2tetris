`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module ALU_tb;
  reg zx, nx, zy, ny, f, no;
  reg[15:0] x;
  reg[15:0] y;

  wire[15:0] out;
  wire ng, zr;

  reg[15:0] out_expected;
  reg ng_expected;
  reg zr_expected;

  ALU UUT (.out(out),
           .zr(zr),
           .ng(ng),

           .x(x),
           .y(y),

           .zx(zx),
           .nx(nx),
           .zy(zy),
           .ny(ny),
           .f(f),
           .no(no)
         );

  reg [55:0] testdata[0:35];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, ALU_tb);

    $readmemb("ALU_tb.data", testdata);
    for (idx = 0; idx < 36; idx = idx + 1) begin
      {x, y, zx, nx, zy, ny, f, no, out_expected, zr_expected, ng_expected} = testdata[idx];
      #10
      // the second part of the conditional is required to detect
      // when out is undefined, a condition not caught by !=
      if (out != out_expected || out === 16'bx ||
          zr != zr_expected || zr === 1'bx ||
          ng != ng_expected || ng === 1'bx) begin
        $display("FAILED for test data #%d: %b", idx, testdata[idx]);
      end
    end

    $finish;
  end
endmodule

