  @1
  $if_A_goto TEST_D
  @FAIL
  0;JEQ

(TEST_D)
  @1
  D=A
  $if_D_goto TEST_M
  @FAIL
  0;JEQ

(TEST_M)
  @SP
  M=1
  $if_M_goto TEST_VAR
  @FAIL
  0;JEQ

(TEST_VAR)
  @X
  M=1

  $if_var_goto X SUCCESS
  @FAIL
  0;JEQ

(SUCCESS)
  @SUCCESS
  0;JEQ

(FAIL)
  @FAIL
  0;JEQ
