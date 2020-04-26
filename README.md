Development Environment
=======================

apio
----

This project uses apio: https://github.com/FPGAwars/apio . I have a custom fork
which enables nicer testbenches: https://github.com/freespace/apio

gtkwave setup
-------------

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

Testbench
=========
Testbench Template
------------------

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


Running Testbenches
-------------------
`apio sim` will run the first test bench it finds (alphabetic sort, ends in
\_tb.v).

In my branch of apio (https://github.com/freespace/apio) you can use
```
apio sim -t <testbench.v>
```

which will run the specified testbench file. This allows us to have more than 1
testbench per module per project.

Testbench Gotchas
-----------------

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

- Assigning constants to a wire will mean it can only take on the assigned
  value or x, e.g.
  ```
  wire a = 0;
  a = 1;
  // value of a is now 'x'
  a = 0;
  // value of a is now 0
  ```

Importing Sources from Other Projects
=====================================

On \*nix use the following script to pull in all verilog files created in
previous projects

```
find  .. -type f -name '*.v' ! -name '*_tb.v' -maxdepth 2 -exec ln -s {} . \;
```

This confuses git b/c git doesn't know about symlinks and thinks there are new
files for it to track. Fix it with:

```
find . -type l | sed -e s'/^\.\///g' >> .gitignore
```

iCE40 UltraPlus
===============

Technology Library
------------------
The iCE40 UltraPlus comes primitives, like the block RAM, which can be
instantiated directly. They are documented in:

http://www.latticesemi.com/~/media/LatticeSemi/Documents/TechnicalBriefs/SBTICETechnologyLibrary201608.pdf

Title of the document is "LATTICE ICE Technology Library" should the URL
become invalid in the future.

Yosys implements *some* of the primitives, e.g. `SB_RAM40_4K`, which are defined
in

https://github.com/YosysHQ/yosys/blob/master/techlibs/ice40/cells_sim.v

Not all primitives are implemented b/c @cliffordwolf believes that it is better
to let the tooling figure things out. (See
https://github.com/YosysHQ/yosys/issues/423).

N.B. I am using the word primitive in the same way lattice is using it.
@cliffordwolf would call them macros in so far as all RAM primitives other than
SB_RAM40_4K is constructed using `SB_RAM40_4K`.

Technical Notes
---------------

- Memory Usage Guide for iCE40 Devices (TN1250): https://www.latticesemi.com/-/media/LatticeSemi/Documents/ApplicationNotes/MO/MemoryUsageGuideforiCE40Devices.ashx?document_id=47775
- SPRAM Usage Guide (TN1314): https://www.latticesemi.com/-/media/LatticeSemi/Documents/ApplicationNotes/IK/iCE40-SPRAM-Usage-Guide.ashx?document_id=51966

