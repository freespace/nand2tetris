#!/usr/bin/env python3

import click

@click.command()
@click.option('-i', '--input-asm', type=click.Path(dir_okay=False, exists=True),
              required=True,
              help='Input assembly file')
@click.option('-o', '--output-hack', type=click.Path(dir_okay=False),
              help='Output hack file')
@click.option('-C', '--compat', is_flag=True,
              help=f'If runs in compatibility mode in which the output is '
                   f'exactly produced by the reference Assembler written in '
                   f'java')
@click.option('-P', '--pretty-print', is_flag=True,
              help=f'If given output will have _ inserted to make instructions '
                   f'easier to read')
@click.option('-A', '--annotate', is_flag=True,
              help=f'If given hack output will be annotated with source '
                   f'lines or PC counts')
def main(*args, **kwargs):
  assembler = Assembler(*args, **kwargs)
  assembler.assemble()
  assembler.write_hack()

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

  # start of variables address space
  VARIABLES_START_ADDRESS = 16

  def __init__(self, input_asm, output_hack=None, compat=False, pretty_print=False, annotate=False):
    self._input_asm = input_asm
    self._output_hack = output_hack
    self._compat = compat
    self._annotate = annotate
    self._pretty_print = pretty_print

    self.known_symbols = dict(self.PREDEFINED_LABELS)
    self.hack_output = []

  def dumps(self):
    """
    Returns the assembled output as a string
    """
    return '\n'.join(self.hack_output)

  def write_hack(self):
    if self._output_hack is None:
      for h in self.hack_output:
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

    # second pass to resolve labels and emit machine code. At this point we would
    # have grabbed all labels for jumps so any unresolved symbols are variables
    # which needs to be assigned a RAM address
    variable_addr = self.VARIABLES_START_ADDRESS
    for inst in instructions:
      symbols = inst.symbols()
      for sym in symbols:
        if not sym in self.known_symbols:
          self.known_symbols[sym] = variable_addr
          variable_addr += 1

      machine_code = inst.resolve(self.known_symbols)

      # if pretty print is not set or in compat mode do not emit _ spacers
      if self._compat or not self._pretty_print:
        machine_code = machine_code.replace('_', '')

      if not self._compat:
        if self._annotate:
          # annotate each hack instruction with the source line
          if inst.generated:
            self.hack_output.append('// <GENERATED> ' + inst.source_line)
          else:
            self.hack_output.append('// ' + inst.source_line)

      self.hack_output.append(machine_code)

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
    if label in self.known_symbols:
      raise Exception(f'Redefinition of {label}')

    # associate the label with the start_addr. We don't use start_addr + 1 b/c
    # the addr is 0-indexed and start_addr is simply the count of number of
    # instructions so far.
    self.known_symbols[label] = start_addr

    # return empty list b/c there is not associated instruction
    return []

  def _parse_C_inst(self, l):
    inst = C_Instruction(l)

    ret = []

    # pre/post nops only emitted when not in compat mode
    if not self._compat:
      for _ in range(inst.num_pre_nops()):
        ret.append(NOP_Instruction())

    ret.append(inst)

    if not self._compat:
      for _ in range(inst.num_post_nops()):
        ret.append(NOP_Instruction())

    return ret

class Instruction:
  def __init__(self, source_line, generated=False):
    """
    generated when True means the instruction was generated by us instead of coming
    from the user
    """
    self.source_line = source_line
    self.generated = generated

  def symbols(self):
    """
    Returns list of symbols used in this instruction
    """
    raise NotImplementedError()

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

  def resolve(self, known_symbols):
    """
    Resolves this instruction into HACK machine code. Returns
    machine code as text, suitable for use with $readmemb in verilog.
    """
    raise NotImplementedError()

class A_Instruction(Instruction):
  def symbols(self):
    v = self.source_line[1:]
    if v.isdigit():
      return []
    else:
      return [v]

  def resolve(self, known_symbols):
    src = self.source_line
    try:
      val = int(src[1:])
    except ValueError:
      label = src[1:]
      if not label in known_symbols:
        raise Exception(f'Unknown label {label}')
      val = known_symbols[label]

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

  def symbols(self):
    return []

  def num_pre_nops(self):
    # writes need an op to allow the RAM address to settle
    if 'M' in self.dest:
      return 1
    else:
      return 0

  def num_post_nops(self):
    # writes need an op to allow the RAM to update
    if 'M' in self.dest:
      return 1
    else:
      return 0

  def resolve(self, known_symbols):
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

class NOP_Instruction(C_Instruction):
  def __init__(self):
    super().__init__('0', generated=True)

if __name__ == '__main__':
  main()

def test_blink():
  with open('tests/blink.hack') as fh:
    expected = fh.read().strip()

  asm = Assembler('tests/blink.asm')
  asm.assemble()
  out = asm.dumps()

  assert expected == out

