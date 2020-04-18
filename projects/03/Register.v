`default_nettype none

module Register(
  output wire[15:0] out,
  input wire clk,
  input wire load,
  input wire[15:0] in);

  Bit b0(out[0], clk, load, in[0]);
  Bit b1(out[1], clk, load, in[1]);
  Bit b2(out[2], clk, load, in[2]);
  Bit b3(out[3], clk, load, in[3]);
  Bit b4(out[4], clk, load, in[4]);
  Bit b5(out[5], clk, load, in[5]);
  Bit b6(out[6], clk, load, in[6]);
  Bit b7(out[7], clk, load, in[7]);
  Bit b8(out[8], clk, load, in[8]);
  Bit b9(out[9], clk, load, in[9]);
  Bit b10(out[10], clk, load, in[10]);
  Bit b11(out[11], clk, load, in[11]);
  Bit b12(out[12], clk, load, in[12]);
  Bit b13(out[13], clk, load, in[13]);
  Bit b14(out[14], clk, load, in[14]);
  Bit b15(out[15], clk, load, in[15]);
endmodule
