  // this is a 24x24 display
  $const kScreenSize 576
  $const kNumCols 24
  $const kNumRows 24

  // World Init
  // ==========
  // wipe the slate clean
  @kScreenSize

  // need -1 otherwise we will reference past end of display
  D=A-1

(WORLD_CLEAR_LOOP)
  @SCREEN
  A=A+D
  M=0
  D=D-1
  $if_D_goto WORLD_CLEAR_LOOP

  // this is a manually inputted glider
  $copy_mv ARG1 1

  $copy_mv ARG0 26
  $call func_SET_PIXEL

  $copy_mv ARG0 51
  $call func_SET_PIXEL

  $copy_mv ARG0 73
  $call func_SET_PIXEL

  $copy_mv ARG0 74
  $call func_SET_PIXEL

  $copy_mv ARG0 75
  $call func_SET_PIXEL

(SIM_LOOP)
  // World shift to make room for new state
  // ======================================
  // go through each pixel and shift it one to the left
  @Idx
  M=0
(WORLD_SHIFT_LOOP)
  // load value at SCREEN + *Idx
  @Idx
  D=M
  @SCREEN
  A=A+D

  // shift *(SCREEN + *Idx) left by 1 bit via addition to itself
  D=M
  M=M+D

  // increment *Idx
  @Idx
  D,M=M+1

  // calculate kScreenSize - *Idx
  @kScreenSize
  D=A-D

  // loop if less than
  @WORLD_SHIFT_LOOP
  D;JLT

  // World Update
  // ==========
  @Idx
  M=0

(WORLD_UPDATE_LOOP)
  $call func_UPDATE_PIXEL

  // increment *Idx
  @Idx
  D,M=M+1

  // calculate kScreenSize - *Idx
  @kScreenSize
  D=A-D

  // loop if less than
  @WORLD_UPDATE_LOOP
  D;JLT

  // Repeat forever
  // ==============
  @SIM_LOOP
  0;JEQ

  // Subroutines
(func_SET_PIXEL)
  // sets *(SCREEN+*ARG0) = *ARG1

  // *ARG0
  @ARG0
  D=M

  // SCREEN + *ARG0
  @SCREEN
  A=A+D

  // *$this.PIXEL_ADDR = (SCREEN + *ARG0)
  @$this.PIXEL_ADDR
  M=D

  // *ARG1
  @ARG1
  D=M

  // **$this.PIXEL_ADDR = *ARG1
  @$this.PIXEL_ADDR
  A=M
  M=D

  $return

(func_UPDATE_PIXEL)
  // *Idx stores the current pixel we are updating

  // neighbours:
  // a b c
  // d X e
  // f g h
  //
  // where X is the pixel being examined.

  // each of the following, on finding a 'live' cell increments
  // @NEIGHBOURS
  @NEIGHBOURS
  M=0

  $call func_CHECK_A
  $call func_CHECK_B
  $call func_CHECK_C
  $call func_CHECK_D
  $call func_CHECK_E
  $call func_CHECK_F
  $call func_CHECK_G
  $call func_CHECK_H

  // update cells state here
  // *NEIGHBOURS
  @NEIGHBOURS
  D=M

  // is it 3?
  @3
  D=D-A

  // any cell with 3 neighbours always lives
  @$this.ALIVE
  D;JEQ

  // is it 2?
  @NEIGHBOURS
  D=M
  @2
  D=D-A

  @$this.IS_2
  D;JEQ

  // nothing to do, this pixel will be dead
  @$this.DONE
  0;JEQ

($this.IS_2)
  //if cell was alive it stays alive
  // *Idx
  @Idx
  D=M

  // SCREEN + *Idx
  @SCREEN
  A=A+D

  // *(SCREEN + *Idx)
  D=M

  // If the cell was dead D will be 0 and we do nothing b/c it stays dead
  @$this.DONE
  D;JEQ

($this.ALIVE)
  // add 1 to the cell to mark it as alive in the next iteration
  // *Idx
  @Idx
  D=M

  // SCREEN + *Idx
  @SCREEN
  A=A+D

  // *(SCREEN + *Idx) += 1
  M=M+1

($this.DONE)
  $return

(func_CHECK_A)
  // check A only if *Idx >= kNumCols as otherwise we are on the first row and have no neighbours
  // above us
  $call func_IS_FIRST_ROW
  $if_var_goto RET $this.DONE

  // check to see if we are in the first column, if we are nothing to be done
  $call func_IS_FIRST_COL
  $if_var_goto RET $this.DONE

  // otherwise count the neighbour
  @kNumCols
  D=A+1
  @ARG0
  M=-D

  $call func_COUNT_NEIGHBOUR

($this.DONE)
  $return

(func_CHECK_B)
  // check B only if *Idx >= kNumCols as otherwise we are on the first row and have no neighbours
  // above us
  $call func_IS_FIRST_ROW
  $if_var_goto RET $this.DONE

  // otherwise count the neighbour
  @kNumCols
  D=A
  @ARG0
  M=-D

  $call func_COUNT_NEIGHBOUR

($this.DONE)
  $return


(func_CHECK_C)
  // check B only if *Idx >= kNumCols as otherwise we are on the first row and have no neighbours
  // above us
  $call func_IS_FIRST_ROW
  $if_var_goto RET $this.DONE

  // check to see if we are in the last column, if we are nothing to be done
  $call func_IS_LAST_COL
  $if_var_goto RET $this.DONE

  // otherwise count the neighbour
  @kNumCols
  D=A-1
  @ARG0
  M=-D

  $call func_COUNT_NEIGHBOUR

($this.DONE)
  $return

(func_CHECK_D)
  $call func_IS_FIRST_COL
  $if_var_goto RET $this.DONE

  $copy_mv ARG0 -1
  $call func_COUNT_NEIGHBOUR

($this.DONE)
  $return

(func_CHECK_E)
  $call func_IS_LAST_COL
  $if_var_goto RET $this.DONE

  $copy_mv ARG0 1
  $call func_COUNT_NEIGHBOUR

($this.DONE)
  $return

(func_CHECK_F)
  $call func_IS_LAST_ROW
  $if_var_goto RET $this.DONE

  $call func_IS_FIRST_COL
  $if_var_goto RET $this.DONE

  @kNumCols
  D=A-1

  @ARG0
  M=D

  $call func_COUNT_NEIGHBOUR

($this.DONE)
  $return

(func_CHECK_G)
  // if we are in the last row we are done
  $call func_IS_LAST_ROW
  $if_var_goto RET $this.DONE

  // otherwise count the neighbour that is kNumCols-1 _ahead_
  $copy_mv ARG0 kNumCols
  $call func_COUNT_NEIGHBOUR

($this.DONE)
  $return

(func_CHECK_H)
  $call func_IS_LAST_ROW
  $if_var_goto RET $this.DONE

  $call func_IS_LAST_COL
  $if_var_goto RET $this.DONE

  @kNumCols
  D=A+1
  @ARG0
  M=D

  $call func_COUNT_NEIGHBOUR

($this.DONE)
  $return

(func_IS_FIRST_ROW)
  $copy_mv RET 0

  // *Idx
  @Idx
  D=M

  // *Idx - kNumCols
  @kNumCols
  D=D-A

  @$this.NO
  D;JGE

  $copy_mv RET 1

($this.NO)
  $return

(func_IS_LAST_ROW)
  $copy_mv RET 0

  // we are last row if *Idx >= kScreenSize - kNumCols
  // kScreenSize
  @kScreenSize
  D=A

  // kScreenSize - kNumCols
  @kNumCols
  D=D-A

  // (kScreenSize - kNumCols) - *Idx
  @Idx
  D=D-M

  // if D is >0 we are _not_ last row
  $if_D_goto $this.NO

  $copy_mv RET 1

($this.NO)
  $return

(func_IS_FIRST_COL)
  // we are in the first column if *Idx is divisible by kNumCols
  $copy_mm ARG0 Idx
  $copy_mv ARG1 kNumCols

  $call func_IS_DIVISOR

  $return

(func_IS_LAST_COL)
  // we are in the last column if *Idx is divisible by (kNumCols-1)
  $copy_mm ARG0 Idx

  @kNumCols
  D=A-1

  @ARG1
  M=D

  $call func_IS_DIVISOR

  $return

(func_COUNT_NEIGHBOUR)
  // checks the value of *(SCREEN + *Idx + *ARG0) and if it is not 0 increments *NEIGHBOURS
  // *Idx. ARG0 stores offset from *Idx
  @Idx
  D=M

  // *Idx + *ARG0
  @ARG0
  D=D+M

  // SCREEN + (*Idx + *ARG0)
  @SCREEN
  A=A+D

  // *(SCREEN + (*Idx + *ARG0))
  D=M

  // if D is 0 then neighbour is "dead" and we are done
  @$this.DONE
  D;JEQ

  @NEIGHBOURS
  M=M+1

($this.DONE)
  $return

(func_IS_DIVISOR)
  $copy_mv RET 0

  // sets @RET to 1 if @ARG0 % @ARG1 == 0
  @ARG0
  D=M

  // we can bail right now if ARG0 is 0
  @$this.YES
  D;JEQ

($this.LOOP)
  @ARG1
  A=M

  D=D-A

  // if D>A then we need to keep looping
  @$this.LOOP
  D;JGT

  // if D-A is < 0 then it is not divisor
  @$this.NO
  D;JLT

  // if we are here then D=0 and we are a divisor
  $copy_mv RET 1

($this.NO)
  $return
