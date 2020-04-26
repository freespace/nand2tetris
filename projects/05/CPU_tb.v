`default_nettype none
`define DUMPSTR(x) `"x.vcd`"

`define NTESTROWS 5

module CPU_tb;
  wire[15:0] outM;
  wire[15:0] addressM;
  wire writeM;
  wire[15:0] pc;

  reg clk;
  reg[15:0] inM;
  reg[15:0] inst;
  reg reset;


  CPU UUT (.outM(outM),
           .addressM(addressM),
           .writeM(writeM),
           .pc(pc),
           .clk(clk),
           .inM(inM),
           .inst(inst),
           .reset(reset));

  reg [15:0] testdata[0:`NTESTROWS-1];
  integer idx;

  initial begin
    $dumpfile(`DUMPSTR(`VCD_OUTPUT));
    $dumpvars(0, CPU_tb);

    $readmemb("test_1.hack", testdata);
    clk = 1;

    // reset PC
    reset = 1;
    #10;
    clk = 0;
    #10;
    clk = 1;
    reset = 0;

    inst = 16'b0;

    for (idx = 0; idx < `NTESTROWS; idx = idx + 1) begin
      #10;
      clk = 0;

      inst = testdata[idx];

      #10;
      clk = 1;
    end

    // one more clock cycle
    #10;
    clk = 0;
    #10;
    clk = 1;

    $finish;
  end
endmodule

