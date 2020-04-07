`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module Nand_tb;
  reg a, b;
  wire y;

  Nand UUT (.a(a), .b(b), .y(y));

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, Nand_tb);

    a = 0;
    b = 0;
    #10;
    if (y != 1) begin
      $display("FAILED for input 00");
    end

    a = 1;
    b = 0;
    #10;
    if (y != 1) begin
      $display("FAILED for input 10");
    end

    a = 1;
    b = 1;
    #10;
    if (y != 0) begin
      $display("FAILED for input 11");
    end

    $finish;
  end
endmodule
