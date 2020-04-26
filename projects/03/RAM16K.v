`default_nettype none

module RAM16K(
  output wire[15:0] out,
  input wire clk,
  input wire load,
  input wire[13:0] addr,
  input wire[15:0] in);

  reg[15:0] ram[0:16383];

  always @(posedge clk) begin
    if (load) begin
      ram[addr] <= in;
    end
  end

  assign out = ram[addr];
endmodule

