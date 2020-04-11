`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module Not_tb;
  reg a;
  wire y;
  Not UUT (.a(a), .out(y));
  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, Not_tb);

    a = 0;
    #10;
    if (y != 1) begin
      $display("FAILED for input 0");
    end

    a = 1;
    #10;
    if (y != 0) begin
      $display("FAILED for input 1");
    end

    $finish;
  end
endmodule
