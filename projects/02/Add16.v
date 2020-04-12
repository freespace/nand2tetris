`default_nettype none

module Add16(
  output wire[15:0] sum,
  input wire[15:0] a,
  input wire[15:0] b);

  wire c0,   c1,  c2,  c3,
       c4,   c5,  c6,  c7,
       c8,   c9, c10, c11,
       c12, c13, c14, c15;

  HalfAdder sum0(sum[0], c0, a[0], b[0]);
  FullAdder sum1(sum[1], c1, a[1], b[1], c0);
  FullAdder sum2(sum[2], c2, a[2], b[2], c1);
  FullAdder sum3(sum[3], c3, a[3], b[3], c2);
  FullAdder sum4(sum[4], c4, a[4], b[4], c3);
  FullAdder sum5(sum[5], c5, a[5], b[5], c4);
  FullAdder sum6(sum[6], c6, a[6], b[6], c5);
  FullAdder sum7(sum[7], c7, a[7], b[7], c6);
  FullAdder sum8(sum[8], c8, a[8], b[8], c7);
  FullAdder sum9(sum[9], c9, a[9], b[9], c8);
  FullAdder sum10(sum[10], c10, a[10], b[10], c9);
  FullAdder sum11(sum[11], c11, a[11], b[11], c10);
  FullAdder sum12(sum[12], c12, a[12], b[12], c11);
  FullAdder sum13(sum[13], c13, a[13], b[13], c12);
  FullAdder sum14(sum[14], c14, a[14], b[14], c13);
  // c15 is not used but can be used for overflow
  // detection
  FullAdder sum15(sum[15], c15, a[15], b[15], c14);
endmodule
