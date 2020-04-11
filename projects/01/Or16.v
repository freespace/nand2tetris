`default_nettype none

module Or16 (
  output wire[15:0] out,
  input wire[15:0] a,
  input wire[15:0] b
);

  Or or0(out[0], a[0], b[0]);
  Or or1(out[1], a[1], b[1]);
  Or or2(out[2], a[2], b[2]);
  Or or3(out[3], a[3], b[3]);
  Or or4(out[4], a[4], b[4]);
  Or or5(out[5], a[5], b[5]);
  Or or6(out[6], a[6], b[6]);
  Or or7(out[7], a[7], b[7]);
  Or or8(out[8], a[8], b[8]);
  Or or9(out[9], a[9], b[9]);
  Or or10(out[10], a[10], b[10]);
  Or or11(out[11], a[11], b[11]);
  Or or12(out[12], a[12], b[12]);
  Or or13(out[13], a[13], b[13]);
  Or or14(out[14], a[14], b[14]);
  Or or15(out[15], a[15], b[15]);

endmodule

