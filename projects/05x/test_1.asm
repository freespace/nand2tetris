  // load into A
  @1234

  // transfer into D
  D=A

  // add D and A e.g. 2*x
  D = D + A

  // load address
  @2345

  // write into M
  M=D

(END)
  @2345
  M=M+1
  @END
  0;JMP
