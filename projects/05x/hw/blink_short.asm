(WRITE_1)
  @R0
  M=0

(WRITE_1_LOOP)
  // write to SCREEN+R0
  @R0
  D=M
  @SCREEN
  A=A+D
  M=1

  // increment R0
  D=D+1
  @R0
  M=D

  // check loop condition
  @7
  D=D-A
  @WRITE_1_LOOP
  D;JLT

  // otherwise jump to WRITE_0 to start clearing the screen
  @WRITE_0
  0;JEQ

(WRITE_0)
  @R0
  M=0

(WRITE_0_LOOP)
  // write to SCREEN+R0
  @R0
  D=M
  @SCREEN
  A=A+D
  M=0

  // increment R0
  D=D+1
  @R0
  M=D

  // check loop condition
  @7
  D=D-A
  @WRITE_0_LOOP
  D;JLT

  // otherwise jump to WRITE_0 to start clearing the screen
  @WRITE_1
  0;JEQ
