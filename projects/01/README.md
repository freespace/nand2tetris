Implementation
==============
These modules intentionally specify the implementation instead of behaviour
because that is in the spirit of nand2tetris. These would of course be much
faster using behaviour verilog.

Testbenches
===========

To use apio with this project use the fork from

  https://github.com/freespace/apio

and use `apio sim -t <test_bench.v>`. Note that this only works for `ice40`
boards for now.

Testbench Data
==============

Some are generated and some are copied from the nand2tetrix course material.
Note that in case of the latter spaces delimited words so 0000_0000 is 1x8bit
word while 0000 0000 is 2x4bit words!
