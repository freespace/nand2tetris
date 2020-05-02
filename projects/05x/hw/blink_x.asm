(INIT)
  // ...
(WRITE_1)
  D = 0

(WRITE_1_LOOP)
  // write to SCREEN+D
  @SCREEN
  A=A+D
  M=1

  // increment D
  D=D+1

  // loop if D is smaller than A
  @255
  W=D-A
  @WRITE_1_LOOP
  W;JLT

  // otherwise jump to WRITE_0 to start clearing the screen
  @WRITE_0
  0;JEQ

(WRITE_0)
  D=0

(WRITE_0_LOOP)
  // write to SCREEN+D
  @SCREEN
  A=A+D
  M=0

  // increment D
  D=D+1

  // loop if D is smaller than A
  @255
  W=D-A
  @WRITE_0_LOOP
  W;JLT

  // otherwise jump to WRITE_0 to start clearing the screen
  @WRITE_1
  0;JEQ

(END)
  // ...
