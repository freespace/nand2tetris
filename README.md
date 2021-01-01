Status
======

Chapters are checked off as they are (a) implemented and passes the supplied tests.

✅ Chapter 1
✅ Chapter 2
✅ Chapter 3
✅ Chapter 4
✅ Chapter 5
✅ Chapter 6
✅ Chapter 7
✅ Chapter 8

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
Project 05x extends the HACK platform to implement an additional `W` register.
This extended platform is called HACKx and it extends the C-instruction from:

```
1 1  1 a c1 c2 c3 c4 c5 c6 d1 d2 d3 j1 j2 j3
⬇️
1 w d4 a c1 c2 c3 c4 c5 c6 d1 d2 d3 j1 j2 j3
```

Where

  - `/w a` forms a 2-bit vector that selects the `x` input of the ALU from `A`,
    `inM` or `W` corresponding to `00`, `01`, `10`. `11` is undefined.
  - `d4` works like `d1..d3` but inverted. When it is UNSET the `W` register takes on the
    ALU output on the next clock.

The interpretation of `w` and `d4` has been chosen so that programs intended for
the HACK platform can run on the HACKx platform without modification. Yay
backward compatibility!

> I named the register W as a homage to the W register found in PIC
> microcontrollers.

Assembler
---------
### Macros

Macros are implemented in two places:

1. `asm.py` used by `vm2asm.py`
2. `assembler.py`

Macros in `asm.py` are self contained and emits assembly instruction to perform set tasks, e.g.
`$inc_sp` to increment the stack pointer by 1.

Macros in `assembler.py` have wider ranging effects, e.g. `$const` defines a new constant in the
symbol table.

### Valid Symbol Characters
The course calls for $ to be a valid character, however I accidentally used it for the macro
system so it cannot be a valid identifier any more.

### Numeric Constants
Our implementation of the assembler (`tools/assembler.py`) accepts hex and binary constants in the
form of:

  - 0xNNNN for hexadecimal constants
  - 0bNNNN for binary constants

Take a page from verilog's book hexadecimal and binary constants can be
spaced out using underscore(_) to improve readability.

The assembler fully supports the HACKx platform. To ensure HACK compatible
machine code is emitted specify `-C` on the commandline. This will cause
the assembler to error when it encounters use of the `W` register.

The assembler can optionally annotate the machine code output with
the corresponding source block _and_ the `PC` value if the `-A` option is given. This is useful
during debugging.

### T0-T3 Registers
Some of the R0-R15 registers serve dual purpose and only R13-15 is actually
available for general use. To avoid having to remember which registers can be
used freely R13-15 can also be addressed as T0-T3.

### Optimisations
When `-O<opt>` is specified the assembler will perform some simple optimisations.
`<opt>` can be one of:

- `all`: perform all optimisations
- `loads`: remove redundant loads where two (or more) A-instructions loading the same
           value will be reduced to one iff the A register is not modified in between
- `consec_nops`: consecutive NOP (0) instructions will be collapsed into one
- `unneeded_nops`: unneeded NOP (0) instructions will be removed. A NOP is
                   unneeded if the next instructions following memory write
                   doesn't access memory.

VM Translator
-------------
Our implementation of the vm-to-asm translator (`tools/vm2asm.py`) is capable of
generating assembly for the HACKx and HACK platform with the HACKx platform
being the default target. To run tests VM programs from the course specify `-C`
when invoking `vm2asm.py`. It is not necessary to also specify `-C` to the
assembler b/c `vm2asm.py` will not use the `W` register.

Like the assembler `vm2asm.py` will produce annotated assembly if `-A` is given.

### Direct Segment Manipulation
Following the stack model religiously means incrementing a value looks like
this:

```
push local 0
push constant 1
add
pop local 0
```

This sequence ultimately results in no change in the stack pointer value (2 push
and 2 pops) and since incrementing by 1 doesn't require another operand we could
have manipulated the value using `M=M+1`. This is true for other 1-operand
operations our ALU is capable of, e.g. `!`, `M-1` etc.

The VM translator implemented here supports the following direct segment
manipulation commands:

- `s_inc <segment> <index>`: increments the segment value directly
- `s_dec <segment> <index>`: decrements the segment value directly
- `s_neg <segment> <index>`: negates (-x) the segment value directly
- `s_not <segment> <index>`: binary not's (~x) the segment value directly
- `s_set <segment> <index>`: sets all bits of the segment value directly
- `s_clear <segment> <inex>`: clears all bits of the segment value directly

### Optimisations
When targetting the HACKx platform the VM translator will use the W register as
a dedicated stack pointer register. This significantly reduces the number of
memory access commands.

Chapters and Projects
=====================

Chapters 1-5 are implemented in their respective `projects/` folder. Chapters 6
onwards live in `tools/` b/c that makes the mose sense to me.

Running Tests
-------------

I have issue using the supplied software as-is, often getting opaque errors about "Expression
expected on line 0". So I would often I edit the `.tst` files to remove the load commands and only
preserve the RAM setup commands. I would then mostly manually verify the content of RAM is as
expected against the `.cmp` files.

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
