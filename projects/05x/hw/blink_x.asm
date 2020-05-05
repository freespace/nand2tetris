(INIT)
  @T0
  M=0

(RESET_LOOP)
  @T0
  M=!M

  // 16384 + 255
  @16639
  W=A
(LOOP)
  // load value to write
  @T0
  D=M

  // write to address stored in W
  A=W
  M=D

  // decrement W
  W=W-1

  // we can't compute W-A b/c both are
  // in the ALU's Y line so put W into D
  D = W

  // is D(=W) > SCREEN?
  @SCREEN
  D=D-A

  // loop if it is
  @LOOP
  D;JGT

  // reset loop if it isn't
  @RESET_LOOP
  0;JEQ
