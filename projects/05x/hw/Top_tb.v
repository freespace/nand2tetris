`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

module Top_tb;
  reg clk = 0;
  wire s_clk;
  wire s_data;
  wire s_reset;
  wire led1;
  wire ledr_n;
  wire ledg_n;

  Top #(800, 1, 400) UUT (clk,
           s_clk,
           s_data,
           s_reset,
           led1,
           ledr_n,
           ledg_n);

  always #1 clk <= ~clk;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, Top_tb);

    #1000000

    $finish;
  end

endmodule
