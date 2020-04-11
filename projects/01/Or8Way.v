`default_nettype none

module Or8Way (
  output wire out,
  input wire[7:0] a
);

  wire o00, o01, o02, o03;
  wire o10, o11;

  Or or00(o00, a[0], a[1]);
  Or or01(o01, a[2], a[3]);
  Or or02(o02, a[4], a[5]);
  Or or03(o03, a[6], a[7]);

  Or or10(o10, o00, o01);
  Or or11(o11, o02, o03);

  Or or20(out, o10, o11);
endmodule

