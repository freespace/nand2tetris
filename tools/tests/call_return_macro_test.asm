  // System Init
  // ===========
  @255
  D=A
  @SP
  M=D

  @.MAIN
  0;JEQ

(func_INC_ARG0)
  @ARG0
  M=M+1
  $return

(func_ADD)
  @ARG0
  D=M

  @ARG1
  D=D+M

  @RET
  M=D
  $return

(.MAIN)
  $copy_mv ARG0 13

  $call func_INC_ARG0

  // ARG0 is now 14

  $copy_mv ARG1 17

  $call func_ADD

  // RET should hold 31

(END)
  @END
  0;JEQ
