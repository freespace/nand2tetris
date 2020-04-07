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

With the above in place `apio sim` should run the simulation and then start
`gtkwave` with the simulation results loaded.

