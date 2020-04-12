gtkwave setup
=============

1. Install using brew cask install gtkwave
1. Install Switch perl module into system dir: `sudo cpan install Switch`
1. If required fix up permissions in `/Library/Perl`, e.g.
```
sudo find /Library/Perl -type d -exec chmod a+rx {} \;
sudo find /Library/Perl -type f -exec chmod a+r {} \;
```
1. Replace `/usr/local/bin/gtkwave` with symlink to
   `/Applications/gtkwave.app/Contents/Resources/bin/gtkwave`

When you type `gtkwave` in the commandline it should launch the app.

Testbench Template
==================

1. Define the DUMPSTR macro:
```
`define DUMPSTR(x) `"x.vcd`"
```
1. Define the simulation output files:
```
$dumpfile(`DUMPSTR(`VCD_OUTPUT));
$dumpvars(0, <testbench_name>);
```

Where `<testbench_name>` is something like `Nand_tb`.

Testbench Gotchas
=================

- When using if-statements with wires a delay is required for the wire
  value to update otherwise nothing seems to happen
  ```
  a = 1;
  b = 1;
  #10;
  if (y != 1) begin
    $display("FAILED for input 11");
  end
  ```

Running Testbenches
===================
`apio sim` will run the first test bench it finds (alphabetic sort, ends in
\_tb.v).

In my branch of apio (https://github.com/freespace/apio) you can use
```
apio sim -t <testbench.v>
```

which will run the specified testbench file. This allows us to have more than 1
testbench per module per project.
