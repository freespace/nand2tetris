`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module And_tb;
  reg a;
  reg b;
  wire y;
  And UUT (.a(a), .b(b), .out(y));
  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, And_tb);

    a = 0;
    b = 0;
    #10;
    if (y != 0) begin
      $display("FAILED for input 00");
    end

    a = 1;
    b = 0;
    #10;
    if (y != 0) begin
      $display("FAILED for input 10");
    end

    a = 0;
    b = 1;
    #10;
    if (y != 0) begin
      $display("FAILED for input 01");
    end

    a = 1;
    b = 1;
    #10;
    if (y != 1) begin
      $display("FAILED for input 11");
    end
    $finish;
  end
endmodule

