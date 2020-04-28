#!/usr/bin/env python3

import click

@click.command()
@click.option('-i', '--input-asm', type=click.Path(dir_okay=False, exists=True),
              required=True,
              help='Input assembly file')
@click.option('-o', '--output-hack', type=click.Path(dir_okay=False),
              help='Output hack file')
@click.option('--compat', is_flag=True,
              help=f'If runs in compatibility mode in which the output is '
                   f'exactly produced by the reference Assembler written in '
                   f'jaba')
def main(*args, **kwargs):
  assembler = Assembler(*args, **kwargs)
  assembler.assemble()
  assembler.write_hack()

class Instruction:
  def __init__(self, source_line):
    self.source_line = source_line

  def num_pre_nops(self):
    """
    Returns number of nop instructions that needs to be inserted BEFORE
    this instruction should be executed.
    """
    raise NotImplementedError()

  def num_post_nops(self):
    """
    Returns number of nop instructions that needs to be inserted AFTER
    this instruction should be executed.
    """
    raise NotImplementedError()

  def resolve(self, known_labels):
    """
    Resolves this instruction into HACK machine code. Returns
    machine code as text, suitable for use with $readmemb in verilog.
    """
    raise NotImplementedError()

class NOP_Instruction(Instruction):
  def num_pre_nops(self):
    return 0
  def num_post_nops(self):
    return 0
  def resolve(self, known_labels):
    # configure the ALU to output a 0. Not a true NOP
    # since it changes the ALU flags
    return C_Instruction('0').resolve({})

class A_Instruction(Instruction):
  def resolve(self, known_labels):
    src = self.source_line
    try:
      val = int(src[1:])
    except ValueError:
      label = src[1:]
      if not label in known_labels:
        raise Exception(f'Unknown label {label}')
      val = known_labels[label]

    return f'0{val:015b}'

class C_Instruction(Instruction):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    src = self.source_line
    # C-inst has the form dest=comp;jump where dest, comp and jump are all
    # optional

    dest = ''
    comp = ''
    jump = 'XXX'

    if '=' in src:
      dest, tail = src.split('=', 1)
      src = tail

    if ';' in src:
      comp, jump = src.split(';', 1)
    else:
      comp = src

    self.dest = dest
    self.comp = comp
    self.jump = jump

  def num_pre_nops(self):
    # memory reads need a nop before to allow RAM
    # to update
    if 'M' in self.comp:
      return 1
    else:
      return 0

  def num_post_nops(self):
    # writes need an op to allow the RAM to update
    if 'M' in self.dest:
      return 1
    else:
      return 0

  def resolve(self, known_labels):
    a = int('M' in self.comp)
    d1 = int('A' in self.dest)
    d2 = int('D' in self.dest)
    d3 = int('M' in self.dest)
    j1 = int(self.jump in 'JLT JLE JNE')
    j2 = int(self.jump in 'JLE JGE JEQ')
    j3 = int(self.jump in 'JGT JGE JNE')

    comp_table = {
        '0'     : '101010',
        '1'     : '111111',
        '-1'    : '111010',
        'D'     : '001100',
        'A'     : '110000',
        '!D'    : '001101',
        '!A'    : '110001',
        '-D'    : '001111',
        '-A'    : '110011',
        'D+1'   : '011111',
        'A+1'   : '110111',
        'D-1'   : '001110',
        'A-1'   : '110010',
        'D+A'   : '000010',
        'D-A'   : '010011',
        'A-D'   : '000111',
        'D&A'   : '000000',
        'D|A'   : '010101',
    }

    comp = self.comp
    if a:
      # replace M with A in comp for lookup purposes
      comp = comp.replace('M', 'A')

    try:
      c1_c6 = comp_table[comp]
    except KeyError:
      raise Exception(f'Unsupported computation {self.com}')

    return f'111_{a}_{c1_c6}_{d1}{d2}{d3}_{j1}{j2}{j3}'

class Assembler:
  # labels map label names to memory addresses
  PREDEFINED_LABELS = dict(R0=0,
                           R1=1,
                           R2=2,
                           R3=3,
                           R4=4,
                           R5=5,
                           R6=6,
                           R7=7,
                           R8=8,
                           R9=9,
                           R10=10,
                           R11=11,
                           R12=12,
                           R13=13,
                           R14=14,
                           R15=15,
                           SP=0,
                           LCL=1,
                           ARG=2,
                           THIS=3,
                           THAT=4,
                           SCREEN=16384,
                           KBD=24576)

  def __init__(self, input_asm, output_hack, compat):
    self._input_asm = input_asm
    self._output_hack = output_hack
    self._compat = compat
    self.known_labels = dict(self.PREDEFINED_LABELS)
    self.hack_instructions = []

  def write_hack(self):
    if self._output_hack is None:
      for h in self.hack_instructions:
        print(h)

  def assemble(self):
    with open(self._input_asm) as fh:
      asm_lines = fh.readlines()

    # remove white space
    asm_lines = [l.strip() for l in asm_lines]

    # remove comments
    asm_lines = [l.split('//')[0] for l in asm_lines]

    # remove empty lines
    asm_lines = [l for l in asm_lines if len(l)]

    instructions = []
    # first pass to parse instructions and grab labels
    for l in asm_lines:
      instructions += self._parse_line(l, len(instructions))

    # second pass to resolve labels and emit machine code
    for inst in instructions:
      hack_inst = inst.resolve(self.known_labels)

      # in compat mode do not emit _ spacers
      if self._compat:
        hack_inst = hack_inst.replace('_', '')

      self.hack_instructions.append(hack_inst)

  def _parse_line(self, l, start_addr):
    # a line can be one of 3 things:
    # A-inst, C-inst, or label
    if l[0] == '@':
      return self._parse_A_inst(l)
    elif l[0] == '(':
      return self._parse_label(l, start_addr)
    else:
      return self._parse_C_inst(l)

  def _parse_A_inst(self, l):
    return [A_Instruction(l)];

  def _parse_label(self, l, start_addr):
    # the name of the label is inside the bracket
    label = l[1:-1]
    # make sure the label doesn't already exist
    if label in self.known_labels:
      raise Exception(f'Redefinition of {label}')

    # associate the label with the start_addr. We don't use start_addr + 1 b/c
    # the addr is 0-indexed and start_addr is simply the count of number of
    # instructions so far.
    self.known_labels[label] = start_addr

    # return empty list b/c there is not associated instruction
    return []

  def _parse_C_inst(self, l):
    inst = C_Instruction(l)

    ret = []

    # pre/post nops only emitted when not in compat mode
    if not self._compat:
      for _ in range(inst.num_pre_nops()):
        ret.append(NOP_Instruction(''))

    ret.append(inst)

    if not self._compat:
      for _ in range(inst.num_post_nops()):
        ret.append(NOP_Instruction(''))

    return ret

if __name__ == '__main__':
  main()
