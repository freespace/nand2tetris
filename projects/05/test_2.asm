(INIT)
  @0
  D = A
  @1
  M = D

(LOOP)
  // test loading into A
  @1

  // test transfer into D
  D=A

  // tests A+D
  @0
  A = D + A

  // tests M + D
  M = M + D

  // tests M + 1
  M = M + 1

  @LOOP
  0;JMP
