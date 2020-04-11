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
