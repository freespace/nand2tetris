`default_nettype none

module Not16 (
  output wire[15:0] out,
  input wire[15:0] a
);

  Not n0(out[0], a[0]);
  Not n1(out[1], a[1]);
  Not n2(out[2], a[2]);
  Not n3(out[3], a[3]);
  Not n4(out[4], a[4]);
  Not n5(out[5], a[5]);
  Not n6(out[6], a[6]);
  Not n7(out[7], a[7]);
  Not n8(out[8], a[8]);
  Not n9(out[9], a[9]);
  Not n10(out[10], a[10]);
  Not n11(out[11], a[11]);
  Not n12(out[12], a[12]);
  Not n13(out[13], a[13]);
  Not n14(out[14], a[14]);
  Not n15(out[15], a[15]);

endmodule

