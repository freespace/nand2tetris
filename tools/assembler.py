#!/usr/bin/env python3

import sys
import click

OPT_LOADS = 'loads'
OPT_CONSEC_NOPS = 'consec_nops'
OPT_UNNEEDED_NOPS = 'unneeded_nops'
OPT_MULTIDEST_ASSIGNMENT = 'multidest_assignment'
OPT_ALL = 'all'
OPT_CHOICES=(OPT_ALL,
             OPT_LOADS,
             OPT_CONSEC_NOPS,
             OPT_UNNEEDED_NOPS,
             OPT_MULTIDEST_ASSIGNMENT)

@click.command()
@click.option('-i', '--input-asm', type=click.Path(dir_okay=False, exists=True),
              required=False,
              help='Input assembly file')
@click.option('-o', '--output-hack', type=click.Path(dir_okay=False),
              help='Output hack file')
@click.option('-C', '--compat', is_flag=True,
              help='If runs in compatibility mode in which the output is '
                   'exactly produced by the reference Assembler written in '
                   'java')
@click.option('-P', '--pretty-print', is_flag=True,
              help='If given output will have _ inserted to make instructions '
                   'easier to read')
@click.option('-A', '--annotate', is_flag=True,
              help='If given hack output will be annotated with source '
                   'lines or PC counts')
@click.option('-O', '--optimise', type=click.Choice(OPT_CHOICES), default=None,
              help='If given enables the specified optimisation. Defaults to "all".')
@click.option('--count', 'print_count', is_flag=True,
              help='If given the number of instructions, minus annotation '
                   'is printed to stderr')
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
               optimise=None,
               print_count=False):
    self._input_asm = input_asm
    self._output_hack = output_hack
    self._compat = compat
    self._annotate = annotate
    self._pretty_print = pretty_print
    self._optimise_options = optimise
    self._next_variable_address = Assembler.VARIABLES_START_ADDRESS
    self._print_count = print_count

    self.known_symbols = dict(Assembler.PREDEFINED_LABELS)
    self.hack_output = []

    self._warnings = []

    self._instructions = None

    if annotate:
      self.hack_output.append(f'// SOURCE FILE={input_asm}')

  @property
  def instructions(self):
    if self._instructions is not None:
      return list(self._instructions)
    else:
      return None

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

    instructions = self._optimise(instructions)

    # do another resolve symbol pass to update label addresses
    self._resolve_symbols(instructions)

    # final pass to emit machine code
    pc = 0
    for inst in instructions:
      # gather warnings
      self._warnings += inst.warnings

      machine_code = inst.resolve(self.known_symbols, compat=self._compat)

      if machine_code is not None:
        compact_machine_code = machine_code.replace('_', '')
        assert len(compact_machine_code) == 16

        # if pretty print is not set or in compat mode do not emit _ spacers
        if self._compat or not self._pretty_print:
          machine_code = compact_machine_code

        should_annotate = not self._compat and self._annotate

        if not inst.emit:
          if should_annotate:
            machine_code = f'// [OPTIMISER REMOVED] {machine_code}'
          else:
            machine_code = None
        else:
          if should_annotate:
            machine_code += f' // PC={pc}'
          pc += 1

        if should_annotate:
          self.hack_output.append('')
          # annotate each hack instruction with the source line
          for l in inst.get_annotations():
            self.hack_output.append(f'// {l}')

      if machine_code:
        self.hack_output.append(machine_code)

    if len(instructions) == 0:
      self.warn('No instructions found in input')
    else:
      last_inst = instructions[-1]

      if type(last_inst) != C_Instruction or last_inst.jump == 'XXX':
        self.warn('Last instruction should be a jump instruction')

    if self._print_count:
      sys.stderr.write(f'Assembled {pc} instructions\n')

    # make the instructions available for inspection
    self._instructions = instructions

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
    for inst in (inst for inst in instructions if inst.emit):
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
    oopt = self._optimise_options
    doall = oopt == OPT_ALL
    if doall or oopt == OPT_LOADS:
      self._remove_redundant_loads(instructions)

    if doall or oopt == OPT_CONSEC_NOPS:
      self._remove_consecutive_nops(instructions)

    if doall or oopt == OPT_UNNEEDED_NOPS:
      self._remove_unneeded_nops(instructions)

    if doall or oopt == OPT_MULTIDEST_ASSIGNMENT:
      self._optimise_using_multi_destination_assignments(instructions)

    return instructions

  def _optimise_using_multi_destination_assignments(self, instructions):
    """
    Optimises code such as:

      A = A + 1
      D = A

    into

      A,D = A + 1

    This works if:

      1. X is the lvalue
      2. X is then the rvalue in a Y=X
      3. Y is not read between 1 and 2
    """
    candidate_inst = None
    read_vars = set()
    for inst in (inst for inst in instructions if inst.emit):
      if type(inst) != C_Instruction:
        continue

      # see if we can optimise the current instruction away
      if candidate_inst is not None:
        canoptimise = True

        # cannot optimise multi-destination assignment
        if len(inst.dest) != 1:
          canoptimise = False

        # can only optimise no-compute assignments
        if len(inst.comp) != 1:
          canoptimise = False

        # cannot optimise if the destination and source of the two instructions
        # are different
        if inst.comp != candidate_inst.dest:
          canoptimise = False

        # cannot optimise if the destination was read before now
        if inst.dest in read_vars:
          canoptimise = False

        if canoptimise:
          inst.emit = False
          candidate_inst.dest += ',' + inst.dest
          candidate_inst.regenerate_expression()

          # reset the optimisation state
          candidate_inst = None

          continue

      # otherwise see if this instruction is candidate for optimisation. An instruction is a
      # candidate for optimisation if it has a single destination
      if len(inst.dest) == 1:
        # we only optimise away single assignments
        candidate_inst = inst
        read_vars = set()

        # continue b/c we shall do no more with this instruction
        continue

      # if an instruction is not a candidate for optimisations then track the variables it is
      # reading
      for src in 'ADMW':
        if src in inst.comp:
          read_vars.add(src)


      # if there is a jump anywhere we need to reset optimisation state b/c we cannot optimise
      # across jump instructions b/c the other path may require D without modification
      if inst.jump != 'XXX':
        candidate_inst = None

      # we also, at the moment, do not optimise across multi-destination assignments either
      if len(inst.dest) > 1:
        candidate_inst = None

  def _remove_unneeded_nops(self, instructions):
    """
    Removes nops inserted after M writes if the next instruction
    is an A-instruction or a C-instruction that doesn't read or
    write to memory
    """
    last_inst = None
    for inst in (inst for inst in instructions if inst.emit):
      if last_inst:
        if last_inst.generated and last_inst.expression == '0':
          if type(inst) == A_Instruction:
            last_inst.emit = False

          if type(inst) == C_Instruction:
            last_inst.emit = 'M' in inst.dest or 'M' in inst.comp

      if type(inst) != Label_Instruction:
        last_inst = inst

  def _remove_consecutive_nops(self, instructions):
    last_inst = None
    for inst in (inst for inst in instructions if inst.emit):
      if inst.generated and inst.expression == '0':
        if last_inst and last_inst.generated and last_inst.expression == '0':
          inst.emit = False

      if type(inst) != Label_Instruction:
        last_inst = inst

  def _remove_redundant_loads(self, instructions):
    last_a_inst = None
    for inst in (inst for inst in instructions if inst.emit):
      if type(inst) == A_Instruction:
        if last_a_inst:
          # compare based on expression not on resulting machine code b/c
          # it is possible for one load to refer to a label and another to
          # a RAM variable and they *happen* to have the same value. If we
          # remove one and the label address changes then we will a bug
          if last_a_inst.expression == inst.expression:
            inst.emit = False
        last_a_inst = inst

      # modifying A should force the next A-instruction to emit
      if type(inst) == C_Instruction:
        if 'A' in inst.dest:
          last_a_inst = None

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
    self.emit = True

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

  def __str__(self):
    return f'[{type(self).__name__}] {self.expression}'

class Label_Instruction(Instruction):
  def symbols(self):
    return [self.expression[1:-1]]

  def resolve(self, known_symbols, compat=False):
    return None

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

    # the default value is XXX b/c we do self.jump in 'JEQ JNE' etc and if we used '' as the
    # default value it will always match
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

  def regenerate_expression(self):
    """
    Regenerates self.expression according to self.dest/comp/jump. Needed when optimisers modify
    an instruction's dest/comp/jump and we want the annotated output to match the binary emitted
    """
    expr = ''
    if len(self.dest):
      expr = self.dest + '='

    expr += self.comp

    if self.jump != 'XXX':
      expr += ';' + self.jump

    self.expression = expr

    if self.source_block:
      self.source_block[-1] = expr

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

def test_optimise_load_01():
  # the second @SP should be removed
  src = '''
      @SP
      M=M+1
      @SP
      M=M+1
  '''
  mcode = Assembler().assemble(src).dumps()
  no_opt_lines = mcode.splitlines()

  mcode_opt = Assembler(optimise=OPT_LOADS).assemble(src).dumps()
  opt_lines = mcode_opt.splitlines()

  assert len(opt_lines) < len(no_opt_lines)

def test_optimise_load_02():
  # the second @SP should be removed
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

  mcode_opt = Assembler(optimise=OPT_LOADS).assemble(src).dumps()
  opt_lines = mcode_opt.splitlines()

  assert len(opt_lines) < len(no_opt_lines)

def test_optimise_load_03():
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

  mcode_opt = Assembler(optimise=OPT_LOADS).assemble(src).dumps()
  opt_lines = mcode_opt.splitlines()

  assert len(opt_lines) == len(no_opt_lines)

def test_optimise_consecutive_nops_01():
  # there should only be one nop between the M instructions
  src = '''
      @0
      M=M+1
      M=M+1
  '''
  mcode = Assembler().assemble(src).dumps()
  no_opt_lines = mcode.splitlines()

  mcode_opt = Assembler(optimise=OPT_CONSEC_NOPS).assemble(src).dumps()
  opt_lines = mcode_opt.splitlines()

  assert len(opt_lines) < len(no_opt_lines)

def test_optimise_consecutive_nops_02():
  # there should only be one nop between the M instructions
  # even thugh a label is present
  src = '''
      @0
      M=M+1
      (LABEL)
      M=M+1
  '''
  mcode = Assembler().assemble(src).dumps()
  no_opt_lines = mcode.splitlines()

  mcode_opt = Assembler(optimise=OPT_CONSEC_NOPS).assemble(src).dumps()
  opt_lines = mcode_opt.splitlines()

  assert len(opt_lines) < len(no_opt_lines)

def test_w_m_syntax_error():
  try:
    Assembler().assemble('D=M+W')
  except SyntaxError:
    pass
  else:
    assert False, 'Should have thrown SyntaxError exception'

def test_last_inst_is_not_jump():
  assert len(Assembler().assemble('@1234').warnings) > 0

def test_optmise_unneeded_nops_01():
  # the last nop should be removed
  src = '''
      @0
      M=M+1
      M=M+1
      @0
  '''
  mcode = Assembler().assemble(src).dumps()
  no_opt_lines = mcode.splitlines()

  mcode_opt = Assembler(optimise=OPT_UNNEEDED_NOPS).assemble(src).dumps()
  opt_lines = mcode_opt.splitlines()

  assert len(opt_lines) < len(no_opt_lines)

def test_optmise_unneeded_nops_02():
  # the last nop should be removed even
  # though a label instruction is present
  src = '''
      @0
      M=M+1
      M=M+1
      (LABEL)
      @0
  '''
  mcode = Assembler().assemble(src).dumps()
  no_opt_lines = mcode.splitlines()

  mcode_opt = Assembler(optimise=OPT_UNNEEDED_NOPS).assemble(src).dumps()
  opt_lines = mcode_opt.splitlines()

  assert len(opt_lines) < len(no_opt_lines)

def test_multidest_assignment_optimisation():
  # this test should reduce down to A,D=A+1
  src = '''
    A=A+1
    D=A
  '''

  inst_vec = Assembler(optimise=OPT_MULTIDEST_ASSIGNMENT, annotate=True).assemble(src).instructions
  assert inst_vec[-1].emit == False
  assert inst_vec[0].expression == 'A,D=A+1'

  # this test should reduce M=A+1 into M,D=A+1
  src = '''
    A=A+1
    M=A+1
    D=M
  '''
  inst_vec = Assembler(optimise=OPT_MULTIDEST_ASSIGNMENT, annotate=True).assemble(src).instructions
  # ignore the nops inserted for memory writes
  inst_vec = [inst for inst in inst_vec if inst.comp != '0']
  assert inst_vec[-1].emit == False
  assert inst_vec[1].expression == 'M,D=A+1'

  # this test should result in no optimisation
  src = '''
    A=A+1
    M=D
    D=A
  '''
  inst_vec = Assembler(optimise=OPT_MULTIDEST_ASSIGNMENT, annotate=True).assemble(src).instructions
  # ignore the nops inserted for memory writes
  inst_vec = [inst for inst in inst_vec if inst.comp != '0']
  len(inst_vec) == 3


  # this test should also result in no optimisation
  src = '''
    D=A
    M=A
    A=D
  '''
  inst_vec = Assembler(optimise=OPT_MULTIDEST_ASSIGNMENT, annotate=True).assemble(src).instructions
  # ignore the nops inserted for memory writes
  inst_vec = [inst for inst in inst_vec if inst.comp != '0']
  len(inst_vec) == 3

  # this test should result in optimisation
  src = '''
    A=M
    0
    0
    0
    0
    D=A
  '''
  inst_vec = Assembler(optimise=OPT_MULTIDEST_ASSIGNMENT, annotate=True).assemble(src).instructions
  assert inst_vec[-1].emit == False
  assert inst_vec[0].expression == 'A,D=M'

  # no optimisation across jumps
  src = '''
    A = M
    0; JEQ
    D = A
  '''
  inst_vec = Assembler(optimise=OPT_MULTIDEST_ASSIGNMENT, annotate=True).assemble(src).instructions
  assert len(inst_vec) == 3

  # no optimisation across multi-destination assignments
  src = '''
    A = M
    D, A = A + 1
    W = D
  '''
  inst_vec = Assembler(optimise=OPT_MULTIDEST_ASSIGNMENT, annotate=True).assemble(src).instructions
  assert len(inst_vec) == 3

def test_regenerate_expression():
  inst = C_Instruction('A = M')
  inst.dest = 'A,D'
  inst.regenerate_expression()
  assert inst.expression == 'A,D=M'

  inst = C_Instruction('A = M+1;     JEQ')
  inst.dest = 'A,D'
  inst.regenerate_expression()
  assert inst.expression == 'A,D=M+1;JEQ'
