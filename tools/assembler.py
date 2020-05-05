#!/usr/bin/env python3

import sys
import click

@click.command()
@click.option('-i', '--input-asm', type=click.Path(dir_okay=False, exists=True),
              required=False,
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
@click.option('-O', '--optimise', is_flag=True,
              help='If given we will attempt to optimise to reduce number of instructions')
@click.option('--count', 'print_count', is_flag=True,
              help=f'If given the number of instructions, minus annotation '
                   f'is printed to stderr')
def main(*args, **kwargs):
  assembler = Assembler(*args, **kwargs)
  assembler.assemble()
  assembler.write_hack()

def _stderr_warn(warning):
  sys.stderr.write(f'[WARNING] {warning}\n')
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
                           KBD=24576,

                           # Extension
                           # =========
                           # the 16 registers (R0-R15) cannot be used freely
                           # b/c many has dual purpose when used in conjunction
                           # with the VM. e.g. R0 is SP. To make it clear which
                           # registers can be used as temp variables we define
                           # T0..T2 which map to R5 and R7.
                           T0 = 13,
                           T1 = 14,
                           T2 = 15,
                           )

  # start of variables address space
  VARIABLES_START_ADDRESS = 16

  def __init__(self,
               input_asm=None,
               output_hack=None,
               compat=False,
               pretty_print=False,
               annotate=False,
               optimise=False,
               print_count=False):
    self._input_asm = input_asm
    self._output_hack = output_hack
    self._compat = compat
    self._annotate = annotate
    self._pretty_print = pretty_print
    self._do_optimisation = optimise
    self._next_variable_address = Assembler.VARIABLES_START_ADDRESS
    self._print_count = print_count

    self.known_symbols = dict(Assembler.PREDEFINED_LABELS)
    self.hack_output = []

    self._warnings = []

    if annotate:
      self.hack_output.append(f'// SOURCE FILE={input_asm}')

  @property
  def warnings(self):
    return list(self._warnings)

  def warn(self, warning):
    self._warnings.append(warning)
    _stderr_warn(warning)

  def dumps(self):
    """
    Returns the assembled output as a string
    """
    return '\n'.join(self.hack_output)

  def write_hack(self):
    if self._output_hack is None:
      print(self.dumps())
    else:
      with open(self._output_hack, 'w') as fh:
        fh.write(self.dumps())

  def assemble(self, asm_text=None):
    if asm_text:
      asm_lines = asm_text.split('\n')
    elif self._input_asm:
      with open(self._input_asm) as fh:
        asm_lines = fh.readlines()
    else:
      asm_lines = sys.stdin.readlines()

    # remove white space
    asm_lines = [l.strip() for l in asm_lines]

    # remove empty lines
    asm_lines = [l for l in asm_lines if len(l)]

    instructions = []
    # first pass to parse instructions and grab labels
    source_block = []
    for l in asm_lines:
      source_block.append(l)
      if '//' in l:
        exp, _ = l.split('//', 1)
      else:
        exp = l

      if len(exp) == 0:
        continue

      if exp[0] == '(':
        # we do not reset source_line here b/c we want to keep
        # labels in the source block
        instructions += self._parse_label(exp, source_block)
      else:
        if exp[0] == '@':
          instructions += self._parse_A_inst(exp, source_block)
        else:
          instructions += self._parse_C_inst(exp, source_block)

        source_block = []

    self._resolve_symbols(instructions)

    if self._do_optimisation:
      instructions = self._optimise(instructions)

    # do another resolve symbol pass to update label addresses
    self._resolve_symbols(instructions)

    # remove Label_Instruction since they don't emit machine code
    instructions = [inst for inst in instructions if type(inst) != Label_Instruction]

    # final pass to emit machine code
    for pc, inst in enumerate(instructions):
      # gather warnings
      self._warnings += inst.warnings

      machine_code = inst.resolve(self.known_symbols, compat=self._compat)

      compact_machine_code = machine_code.replace('_', '')
      assert len(compact_machine_code) == 16

      # if pretty print is not set or in compat mode do not emit _ spacers
      if self._compat or not self._pretty_print:
        machine_code = compact_machine_code

      if not self._compat:
        if self._annotate:
          self.hack_output.append('')
          # annotate each hack instruction with the source line
          for l in inst.get_annotations():
            self.hack_output.append(f'// {l}')

          machine_code += f' // PC={pc}'

        self.hack_output.append(machine_code)

    if len(instructions) == 0:
      self.warn('No instructions found in input')
    else:
      last_inst = instructions[-1]

      if type(last_inst) != C_Instruction or last_inst.jump == 'XXX':
        self.warn(f'Last instruction should be a jump instruction')

    if self._print_count:
      sys.stderr.write(f'Assembled {len(instructions)} instructions\n')

    # allow chaining, e.g. self.assemble().dumps()
    return self

  def _parse_A_inst(self, l, source_block):
    return [A_Instruction(l, source_block=source_block)];

  def _parse_label(self, l, source_block):
    return [Label_Instruction(l, source_block=source_block)]

  def _parse_C_inst(self, l, source_block):
    inst = C_Instruction(l, source_block=source_block)

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

  def _resolve_symbols(self, instructions):
    # find all labels and update
    # keep track of labels we have seen this pass to avoid
    # redefinition
    seen_labels = set()
    pc = 0
    for inst in instructions:
      if type(inst) == Label_Instruction:
        symbol = inst.symbols()[0]
        if symbol in seen_labels:
          raise NameError(f'Redefinition of label {symbol}')
        self.known_symbols[symbol] = pc
        seen_labels.add(symbol)
      else:
        pc += 1

    # find all variables and assign RAM location if not
    # already known
    for inst in instructions:
      if type(inst) == A_Instruction:
        for s in inst.symbols():
          if not s in self.known_symbols:
            self.known_symbols[s] = self._next_variable_address
            self._next_variable_address += 1

  def _optimise(self, instructions):
    instructions = self._remove_redundant_loads(instructions)
    instructions = self._remove_consecutive_nops(instructions)

    return instructions

  def _remove_consecutive_nops(self, instructions):
    new_instructions = []
    last_C_inst = None
    for inst in instructions:
      emit = True
      if type(inst) == C_Instruction:
        if last_C_inst:
          if last_C_inst.expression == '0' and inst.expression == '0':
            emit = False

        last_C_inst = inst

      if emit:
        new_instructions.append(inst)

    return new_instructions

  def _remove_redundant_loads(self, instructions):
    new_instructions = []
    last_a_inst = None
    for inst in instructions:
      emit = True
      if type(inst) == A_Instruction:
        if last_a_inst:
          # compare based on expression not on resulting machine code b/c
          # it is possible for one load to refer to a label and another to
          # a RAM variable and they *happen* to have the same value. If we
          # remove one and the label address changes then we will a bug
          if last_a_inst.expression == inst.expression:
            emit = False
        last_a_inst = inst

      # modifying A should force the next A-instruction to emit
      if type(inst) == C_Instruction:
        if 'A' in inst.dest:
          last_a_inst = None

      if emit:
        new_instructions.append(inst)

    return new_instructions

class Instruction:
  def __init__(self, expression, generated=False, source_block=None):
    """
    :param generated: when True means the instruction was generated by us instead of coming
                      from the user.
    :param source_block: source block is all text between the last instruction
                         and this one, inclusive of the instruction itself.
                         This includes comments and jump labels.
    """
    self.expression = expression.replace(' ','')
    self.generated = generated
    self.source_block = source_block
    self._warnings = []

  @property
  def warnings(self):
    return list(self._warnings)

  def get_annotations(self):
    """
    Returns a list of annotations lines
    """
    if self.source_block:
      return self.source_block
    else:
      ret = []
      if self.generated:
        ret.append('<GENERATED>')
      ret.append(self.expression)
      return ret

  def warn(self, warning):
    self._warnings.append(warning)
    _stderr_warn(warning)

  def parse_numeric_constant(self, token):
    """
    Attempts to parse token as:
      - decimal (NNNNNN)
      - hex (requires 0x prefix, e.g. 0xNNNNN)
      - binary (requires 0b prefix, e.g. 0bNNNNN)

    For all hex and binary literals underscores (_) may
    be inserted for readability. e.g. 0xFF_FF_ and 0b1111_1010_0010
    are acceptable.

    Who even uses octal.

    Returns an integer if parsing was successful, None otherwise.

    If overflow would occur the value is truncated to fit and a warning
    is emitted.
    """
    try:
      ret = None
      if token.isdigit():
        ret = int(token)

      token = token.replace('_', '')

      if token[:2] == '0x':
        ret = int(token, 16)

      if token[:2] == '0b':
        ret = int(token, 2)

      # our ISR can only accept 15 bit constants
      if ret:
        if ret > 2**15-1:
          self.warn(f'WARNING: literal value {token} truncated to 15 bits')

        # do this to enforce no more than 15 bits and to make it unsigned
        # so bin(ret) won't return something like -10101
        ret = ret & 0x7FFF

      return ret
    except ValueError:
      raise SyntaxError(f'Failed to parse numeric constant {token}')

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

  def resolve(self, known_symbols, compat=False):
    """
    Resolves this instruction into HACK machine code. Returns
    machine code as text, suitable for use with $readmemb in verilog.

    If compat is True then all use of non-HACK compatible instructions
    will fail.
    """
    raise NotImplementedError()

class Label_Instruction(Instruction):
  def symbols(self):
    return [self.expression[1:-1]]

  def resolve(self, known_symbols, compat=False):
    return []

class A_Instruction(Instruction):
  def symbols(self):
    v = self.expression[1:]
    if v.isdigit():
      return []
    else:
      return [v]

  def resolve(self, known_symbols, compat=False):
    src = self.expression
    val = self.parse_numeric_constant(src[1:])
    if val is None:
      label = src[1:]
      if not label in known_symbols:
        raise NameError(f'Unknown label {label}')
      val = known_symbols[label]

    return f'0{val:015b}'

class C_Instruction(Instruction):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    src = self.expression
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

  def resolve(self, known_symbols, compat=False):
    a = int('M' in self.comp)
    w = int('W' in self.comp)
    d1 = int('A' in self.dest)
    d2 = int('D' in self.dest)
    d3 = int('M' in self.dest)
    d4 = int('W' in self.dest)
    j1 = int(self.jump in 'JLT JLE JNE')
    j2 = int(self.jump in 'JLE JGE JEQ')
    j3 = int(self.jump in 'JGT JGE JNE')

    if compat and (w or d4):
      raise SyntaxError('W is not available when in compatibility mode')

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

    # remove all white space
    comp = comp.replace(' ', '')

    if a and w:
      raise SyntaxError('Cannot use W and M in computation at the same time')

    if a:
      # replace M with A in comp for lookup purposes
      comp = comp.replace('M', 'A')

    if w:
      # replace W with A in comp for lookup purposes
      comp = comp.replace('W', 'A')

    try:
      c1_c6 = comp_table[comp]
    except KeyError:
      try:
        # for some operation the ordering doesn't matter
        # so we will accept D+A and A+D even though only
        # D+A is defined in the comp t able
        if len(comp) == 3 and comp[1] in '+|&':
          comp = comp[::-1]
          c1_c6 = comp_table[comp]
        else:
          raise
      except KeyError:
        raise Exception(f'Unsupported computation {comp}')

    # invert w and d
    w = 1 - w
    d4 = 1 - d4
    return f'1_{w}_{d4}_{a}_{c1_c6}_{d1}{d2}{d3}_{j1}{j2}{j3}'

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

def test_hex_bin_consts():
  with open('tests/blink.hack') as fh:
    expected = fh.read().strip()

  asm = Assembler('tests/blink_hex_bin.asm')
  asm.assemble()
  out = asm.dumps()

  assert expected == out

def test_decimal_consts():
  asm = Assembler().assemble('@256').dumps()
  print(asm)

def test_hex_consts():
  asm = Assembler().assemble('@0xFFF1').dumps()
  print(asm)

def test_const_overflow():
  asm = Assembler().assemble('@0x8001').dumps()
  assert asm == '0000000000000001'

  asm = Assembler().assemble('@0xFFFF').dumps()
  assert asm == '0111111111111111'

  assert len(Assembler().assemble('@0xFFFF').warnings) > 0

def test_optimise_01():
  src = '''
      @SP
      M=M+1
      @SP
      M=M+1
  '''
  mcode = Assembler().assemble(src).dumps()
  no_opt_lines = mcode.splitlines()

  mcode_opt = Assembler(optimise=True).assemble(src).dumps()
  opt_lines = mcode_opt.splitlines()

  assert len(opt_lines) < len(no_opt_lines)

def test_optimise_02():
  src = '''
      @0
      D=M
      @SP
      M=M+1
      @SP
      M=M+1
  '''
  mcode = Assembler().assemble(src).dumps()
  no_opt_lines = mcode.splitlines()

  mcode_opt = Assembler(optimise=True).assemble(src).dumps()
  opt_lines = mcode_opt.splitlines()

  assert len(opt_lines) < len(no_opt_lines)

def test_optimise_03():
  # b/c of modification to A in A=D+1 we cannot
  # optimise away the last @SP
  src = '''
      @0
      D=M
      A=D+1
      @SP
  '''
  mcode = Assembler().assemble(src).dumps()
  no_opt_lines = mcode.splitlines()

  mcode_opt = Assembler(optimise=True).assemble(src).dumps()
  opt_lines = mcode_opt.splitlines()

  assert len(opt_lines) == len(no_opt_lines)

def test_optimise_04():
  src = '''
      @0
      M=M+1
      M=M+1
  '''
  mcode = Assembler().assemble(src).dumps()
  no_opt_lines = mcode.splitlines()

  mcode_opt = Assembler(optimise=True).assemble(src).dumps()
  opt_lines = mcode_opt.splitlines()

  assert len(opt_lines) == len(no_opt_lines)
  print('')
  print(mcode)
  print('')
  print(mcode_opt)

def test_w_m_syntax_error():
  try:
    Assembler().assemble('D=M+W')
  except SyntaxError:
    pass
  else:
    assert False, 'Should have thrown SyntaxError exception'

def test_last_inst_is_not_jump():
  assert len(Assembler().assemble('@1234').warnings) > 0
