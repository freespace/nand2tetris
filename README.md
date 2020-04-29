Significant Implementation Differences
======================================
Hardware RAM
------------
We do not use the RAM modules built in the project, opting to use single port
RAM built into the iCE40 FPGA. This is far more efficient use of resources.

Software Pipelining
-------------------
Due to the characteristics of the CPU a value loaded using an A-instruction
doesn't appear in register A (aka `addressM`) until the next clock edge. For
arithematics this is fine - the ALU will see the value previous loaded and
compute the right values. For memory access however the single port RAM IP core
being used will not update its on the same clock edge in which `addressM` is
updated. It will only do so on the next edge. In other words:

1. edge-1: `addressM` takes on new value, RAM output is undefined because on
   edge transition of the value at the address present immediately *prior* is
   clocked into the RAM.
2. edge-2: the RAM output is now valid and reflects the value at `addressM`

As such every memory read needs to be preceeded by a nop (0). This is the
pipeline equivalent of inserting a bubble into a pipelined CPU but we are doing
it in software.

Writes have a similar issue. When `outM`, `addressM` and `writeM` are
asserted on the same clock edge *no write happens* b/c their value immediately
prior to transition is what matters. So it takes another nop for the write to
commit.

### Update 2020-04-29
I "optimised" memory access by shifting the RAM clock 1/2 period 
(i.e. `ram_clk = ~clk`). This allows `addressM` to be present at the rise edge
of the RAM clock. This means a sequence like

```
@R0
D=M
```

No longer needs a nop. However there is no getting around the fact that each
write takes an additional cycle. Additionally when M is on the RHS and the LHS,
e.g. `M=M+1` a nop before and after is still required.

Inserting these nops is time consuming and prone to error. `tools/assembler.py`
will, by default, insert nops for you so programs supplied by the course can be
used as-is without modification provided they are assembled using our assembler.
Note that I wrote the assembler before I realised it was project 6.

eXtended Register
-----------------
Project 5.1 extends the HACK platform to implement an additional `W` register.
This extended platform is called HACKx and it extends the C-instruction from:

```
1 1  1 a c1 c2 c3 c4 c5 c6 d1 d2 d3 j1 j2 j3
⬇️
1 w d4 a c1 c2 c3 c4 c5 c6 d1 d2 d3 j1 j2 j3
```

Where

  - `w` works like `a`. When it is SET the `D` register supplies the `x` input
      to the ALU. When it is UNSET the `W` register supplies the `x` input to
      the ALU.
  - `d4` works like `d1..d3` but inverted. Wwhen it is UNSET the `W` register takes on the
    ALU output on the next clock. 

The interpretation of `w` and `d4` has been chosen so that programs intended for
the HACK platform can run on the HACKx platform without modification. Yay
backward compatibility!

> I named the register W as a homage to the W register found in PIC
> microcontrollers.


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

Troubleshotting
===============

ERROR: IO 'video_sync' is unconstrained in PCF (override this error with --pcf-allow-unconstrained)
---------------------------------------------------------------------------------------------------
- You have an unused module which defines input/outputs. Remove the module
    should remove the error

ERROR: Unable to place cell 'ROM.5.0.0_RAM', no Bels remaining of type 'ICESTORM_RAM'
-------------------------------------------------------------------------------------
- The ROM size is too large. The icebreaker has 30 EBR units of 256x16 size.
    This allows a maximum of 256*30 = 7680 instructions in the ROM. Use `apio build --verbose-pnr`
    to get usage statistics.
