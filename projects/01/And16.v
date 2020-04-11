`default_nettype none

module And16 (
  output wire[15:0] out,
  input wire[15:0] a,
  input wire[15:0] b
);

  And and0(out[0], a[0], b[0]);
  And and1(out[1], a[1], b[1]);
  And and2(out[2], a[2], b[2]);
  And and3(out[3], a[3], b[3]);
  And and4(out[4], a[4], b[4]);
  And and5(out[5], a[5], b[5]);
  And and6(out[6], a[6], b[6]);
  And and7(out[7], a[7], b[7]);
  And and8(out[8], a[8], b[8]);
  And and9(out[9], a[9], b[9]);
  And and10(out[10], a[10], b[10]);
  And and11(out[11], a[11], b[11]);
  And and12(out[12], a[12], b[12]);
  And and13(out[13], a[13], b[13]);
  And and14(out[14], a[14], b[14]);
  And and15(out[15], a[15], b[15]);

endmodule

