  // we shall use R2 as the accumulator, init to 0
  @R2
  M=0

(LOOP)
  // load R1 into D
  @R1
  D=M

  // jump to end of D is 0
  @END
  D;JEQ

  // R1 is not zero, sub-1
  @R1
  M=D-1

  // load R0 into D
  @R0
  D=M

  // add R0 to R2 writing back to R2
  @R2
  M=D+M

  @LOOP
  0;JMP


(END)
  @END
  0;JMP


