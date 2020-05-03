#!/usr/bin/env python3

import click

from assembler import Assembler

@click.command()
@click.option('-i', '--input-vm', type=click.Path(dir_okay=False, exists=True),
              required=True,
              help='Input VM file')
@click.option('-o', '--output-asm', type=click.Path(dir_okay=False),
              help='Output asm file')
@click.option('-C', '--compat', is_flag=True,
              help=f'If runs in compatibility mode in which the output is '
                   f'exactly produced by the reference translator written in '
                   f'java')
@click.option('-A', '--annotate', is_flag=True,
              help=f'If given hack output will be annotated with source '
                   f'lines or PC counts')
@click.option('--LCL', 'LCL', type=int,
              help='Set base address of the local (LCL) segment')
@click.option('--ARG', 'ARG', type=int,
              help='Set base address of the argument (ARG) segment')
@click.option('--THIS', 'THIS', type=int,
              help='Set base address of the this (THIS) segment')
@click.option('--THAT', 'THAT', type=int,
              help='Set base address of the local (THAT) segment')
@click.option('--RAM', 'ram_specs', type=str, multiple=True,
              help='Use format AAA=VVV to specify RAM[AAA] = VVV')
@click.option('--no-init', is_flag=True,
              help='If given no initialisation code is generated')
def main(*args, **kwargs):
  translator = VM2ASM(*args, **kwargs)
  translator.translate()
  translator.write_asm()

class VM2ASM:
  STATIC_BASE_ADDRESS = 16
  STACK_BASE_ADDRESS = 256
  HEAP_BASE_ADDRESS = 16483
  TEMP_BASE_ADDRESS = 5

  SEGMENT_BASE_ADDR_TABLE = {
      'argument': 'ARG',
      'local'   : 'LCL',
      'static'  : '16',
      'this'    : 'THIS',
      'that'    : 'THAT',
  }

  SEGMENT_SIZE_TABLE = {
      'static'  : 255- 16 + 1,
      'temp'    : 8,
      'pointer' : 2,
  }

  PREDEFINED_CONSTANTS = {
      '$SCREEN': 'SCREEN',
  }

  def __init__(self,
               input_vm=None,
               output_asm=None,
               compat=False,
               annotate=False,
               no_init=False,
               ram_specs=None,
               LCL=None,
               ARG=None,
               THIS=None,
               THAT=None):
    self._input_vm = input_vm
    self._output_asm = output_asm
    self._compat = compat
    self._annotate = annotate
    self._known_symbols = dict(VM2ASM.PREDEFINED_CONSTANTS)

    self.asm_output = []
    if annotate:
      self.asm_output.append(f'// SOURCE FILE={input_vm}')

    if not no_init:
      def set_ram(addr, value):
        asm = ASM(f'''
            // setup {addr}
            @{value}
            D=A
            @{addr}
            M=D
            ''')
        self.asm_output += asm.to_list(indent=4)

      self.asm_output.append(f'// INIT BEGIN')
      set_ram('SP', VM2ASM.STACK_BASE_ADDRESS)

      # if any of the runtime segment base address were given we set them. This is
      # needed to run the test programs supplied by the course
      if LCL:
        set_ram('LCL', LCL)

      if ARG:
        set_ram('ARG', ARG)

      if THIS:
        set_ram('THIS', THIS)

      if THAT:
        set_ram('THAT', THAT)

      if ram_specs and len(ram_specs):
        for spec in ram_specs:
          addr, val = spec.split('=')
          addr = int(addr)
          val = int(val)
          set_ram(addr, val)

      if annotate:
        self.asm_output.append(f'// INIT END')


  def write_asm(self):
    if self._output_asm is None:
      print(self.dumps())
    else:
      with open(self._output_asm, 'w') as fh:
        fh.write(self.dumps())

  def dumps(self):
    """
    Returns the translated output as a string
    """
    return '\n'.join(self.asm_output)

  def translate(self, vm_text=None):
    if vm_text:
      vm_lines = vm_text.splitlines()
    else:
      with open(self._input_vm) as fh:
        vm_lines = fh.readlines()

    # strip whitespace and remove empty lines
    vm_lines = [l.strip() for l in vm_lines]
    vm_lines = [l for l in vm_lines if len(l)]

    operations = []
    source_block = []
    # 1st pass, convert to Operation objects and gather
    # symbols

    # the VM specification is a big vague about
    # when a function "finished". AFAICT it doesn't
    # so this really just tracks the last function operation
    # encountered
    current_function_name = None
    for l in vm_lines:
      source_block.append(l)
      op = self._parse(l, current_function_name)
      if op:
        operations.append(op)

        if type(op) == FUNCTION_Operation:
          current_function_name = op.function_name

    # 2nd pass, emit asm
    for op in operations:
      if self._annotate:
        for a in op.get_annotations():
          self.asm_output.append(f'// {a}')

      self.asm_output += op.resolve(self._known_symbols).to_list(indent=4)

    # this allows chaining, e.g. self.translate().dumps()
    return self

  def _parse(self, source_line, current_function_name):
    if '//' in source_line:
      exp, _ = source_line.split('//', 1)
    else:
      exp = source_line

    tokens = [t for t in exp.split(' ') if len(t)]

    if len(tokens) == 0:
      return None

    op, args = tokens[0], tokens[1:]

    operation_table = {
      # arithmetics
      'add': ADD_Operation,
      'sub': SUB_Operation,
      'neg': NEG_Operation,
      'eq' : EQ_Operation,
      'gt' : GT_Operation,
      'lt' : LT_Operation,
      'and': AND_Operation,
      'or' : OR_Operation,
      'not': NOT_Operation,

      # extensions
      'neq': NEQ_Operation,
      'lte': LTE_Operation,
      'gte': GTE_Operation,

      # memory management
      'push': PUSH_Operation,
      'pop' : POP_Operation,

      # program flow
      'label'  : LABEL_Operation,
      'goto'   : GOTO_Operation,
      'if-goto': IFGOTO_Operation,

      # function calling
      'function': FUNCTION_Operation,
    }

    try:
      op_cls = operation_table[op]
    except KeyError:
      raise SyntaxError(f'Unknown operation {op}')

    return op_cls(args, compat=self._compat, function_name=current_function_name)

class ASM:
  """
  This class implements a superset of assembly instructions

  In addition to normal assembly it has a basic macro system
  where $XXX is treated as a macro and replaced with some pre-defined
  sequence of assembly instructions.

  e.g. $load_sp will load the value in the SP register into A so
  we are accessing the top of the stack.

  This system is abused to implement operation-specific labels. All
  labels should be written as $_<label> and $_ will be replaced with
  a unique number.
  """
  MACRO_LOAD_SP='''
                // MACRO=LOAD_SP
                @SP
                A=M
                // MACRO_END
                '''

  MACRO_SAVE_SP='''
                // MACRO=SAVE_SP
                // update SP, assumes new SP
                // value is in A
                D=A
                @SP
                M=D
                // MACRO_END
               '''

  MACRO_DEC_SP='''
               // MACRO=DEC_SP
               @SP
               M=M-1
               // MACRO_END
               '''

  MACRO_INC_SP='''
               // MACRO=INC_SP
               @SP
               M=M+1
               // MACRO_END
               '''

  MACROS={'$load_sp': MACRO_LOAD_SP,
          '$save_sp': MACRO_SAVE_SP,
          '$dec_sp' : MACRO_DEC_SP,
          '$inc_sp' : MACRO_INC_SP,
          }

  ID_CNT = 0

  def __init__(self, asm_text):
    self._text = asm_text

  def replace(self, target, replacement):
    self._text = self._text.replace(target, replacement)

  def to_list(self, indent=0, comments=True):
    # this ensures if the instruction is reused it still
    # emits different IDs
    self.MACROS['$_'] = f'__{ASM.ID_CNT}__'
    ASM.ID_CNT += 1

    txt = self._text

    # insert macros
    for macro_name, macro_asm in self.MACROS.items():
      if macro_name in txt:
        txt = txt.replace(macro_name, macro_asm)

    if not comments:
      parts = []
      for l in txt.splitlines():
        if l[:2] != '//':
          parts.append(l)
    else:
      parts = txt.splitlines()

    lprefix = ' '*indent
    return [lprefix + l.strip() for l in parts if len(l.strip())]

  def to_string(self, **kwargs):
    return '\n'.join(self.to_list(**kwargs))

  def __str__(self):
    return self.to_string()


class Operation:
  def __init__(self, args=None, compat=False, function_name=None):
    self.args = args
    self.compat = compat
    self.function_name = function_name

  @staticmethod
  def validate_segment_index(segment, index, known_symbols):
    try:
      if index[0] == '$':
        # try to resolve the constant
        index = known_symbols[index]
    except KeyError:
      raise NameError(f'Unknown constant {index}')

    if segment in VM2ASM.SEGMENT_SIZE_TABLE:
      try:
        index = int(index)
      except ValueError:
        raise ValueError(f'Invalid index value {index}')

      if index >= VM2ASM.SEGMENT_SIZE_TABLE[segment]:
        raise ValueError(f'{index} out of range for segment {segment}')

    return segment, index

  @property
  def _label_in_namespace(self):
    label = self.args[0]
    if self.function_name:
      label = f'{self.function_name}:{label}'
    return label

  def resolve(self, known_symbols=None):
    """
    Returns an ASM object that implements this operation.
    """
    raise NotImplementedError()

  def get_annotations(self):
    """
    Returns annotation that should be inserted into the asm output
    as a list of strings
    """
    # infer from class name and self.args
    op =  self.__class__.__name__.split('_', 1)[0]
    parts = [op]

    if self.args:
      parts += self.args

    return [' '.join(parts)]

class Arithmetic_Operation(Operation):
  def resolve(self, known_symbols=None):
    return ASM('''
        $load_sp

        // pop y into D
        A=A-1
        D=M

        // pop x into M
        A=A-1

        // do the operation
        M=M%OP%D

        $dec_sp
        ''')

class ADD_Operation(Arithmetic_Operation):
  def resolve(self, known_symbols=None):
    asm = super().resolve(known_symbols)
    asm.replace('%OP%', '+')
    return asm

class SUB_Operation(Arithmetic_Operation):
  def resolve(self, known_symbols=None):
    asm = super().resolve(known_symbols)
    asm.replace('%OP%', '-')
    return asm


class AND_Operation(Arithmetic_Operation):
  def resolve(self, known_symbols=None):
    asm = super().resolve(known_symbols)
    asm.replace('%OP%', '&')
    return asm


class OR_Operation(Arithmetic_Operation):
  def resolve(self, known_symbols=None):
    asm = super().resolve(known_symbols)
    asm.replace('%OP%', '|')
    return asm


class NEG_Operation(Operation):
  def resolve(self, known_symbols=None):
    return ASM('''
        $load_sp

        // pop y into inM
        A=A-1

        // neg
        M=-M

        // no need to update SP b/c
        // the top of the stack is not
        // changed by a pop and push
        ''')

class NOT_Operation(Operation):
  def resolve(self, known_symbols=None):
    return ASM('''
        $load_sp

        // pop y into D
        A=A-1
        D=M

        // invert and write result to stack
        M=!D

        // no need to update SP b/c
        // the top of the stack is not
        // changed by a pop and push
        ''')

class Compare_Operation(Operation):
  def resolve(self, known_symbols=None):
    if self.compat:
      return ASM('''
          $load_sp

          // pop y into D
          A=A-1
          D=M

          // pop x into M
          A=A-1

          // sub
          D=M-D

          // write -1 (=0xFFFF) into M assuming
          // are EQ
          M=-1

          // update stack pointer to point to top
          // of stack
          $dec_sp

          @$_END
          D;%JMP%

          // if we didn't jump then the comparison
          // fail and we write 0 into the top
          // of the stack

          @SP
          A=M
          A=A-1

          // write 0
          M=0

          ($_END)
          ''')
    else:
      return ASM('''
          $load_sp

          // pop y into D
          A=A-1
          D=M

          // pop x into M
          A=A-1

          // sub
          W=M-D

          // write -1 (=0xFFFF) into M assuming
          // are EQ
          M=-1

          // cache A, skip writing 0s if EQ
          D=A
          @$_END
          W;%JMP%

          // if we didn't jump then the comparison
          // fail and we write 0 into the top
          // of the stack

          // restore A
          A=D

          // write 0
          M=0

          ($_END)

          $dec_sp
          ''')

class EQ_Operation(Compare_Operation):
  def resolve(self, known_symbols=None):
    asm = super().resolve(known_symbols)
    asm.replace('%JMP%', 'JEQ')
    return asm


class GT_Operation(Compare_Operation):
  def resolve(self, known_symbols=None):
    asm = super().resolve(known_symbols)
    asm.replace('%JMP%', 'JGT')
    return asm


class LT_Operation(Compare_Operation):
  def resolve(self, known_symbols=None):
    asm = super().resolve(known_symbols)
    asm.replace('%JMP%', 'JLT')
    return asm


class NEQ_Operation(Compare_Operation):
  def resolve(self, known_symbols=None):
    asm = super().resolve(known_symbols)
    asm.replace('%JMP%', 'JNE')
    return asm


class LTE_Operation(Compare_Operation):
  def resolve(self, known_symbols=None):
    asm = super().resolve(known_symbols)
    asm.replace('%JMP%', 'JLE')
    return asm


class GTE_Operation(Compare_Operation):
  def resolve(self, known_symbols=None):
    asm = super().resolve(known_symbols)
    asm.replace('%JMP%', 'JGE')
    return asm

class PUSH_Operation(Operation):
  """
  Takes value at segment[index] and pushes it onto
  the stack. SP is incremented.
  """
  def resolve(self, known_symbols=None):
    segment, index = self.args
    segment, index = Operation.validate_segment_index(segment, index, known_symbols)

    def push_content_of_ptr(ptr_addr, offset):
      if offset == 0:
        return ASM(f'''
            // load the pointer value
            @{ptr_addr}

            // dereference the pointer
            A=M

            // save the value into D
            D=M

            $load_sp

            // write value to top of stack
            M=D

            $inc_sp
            ''')
      else:
        return ASM(f'''
            // load the pointer value into D
            @{ptr_addr}
            D=M

            // load the offset into A
            @{offset}

            // calculate the new pointer value
            // and dereference
            A=A+D

            // save the value into D
            D=M

            $load_sp

            // write value to top of stack
            M=D

            $inc_sp
            ''')

    # this is the sme as push_content_of_ptr but
    # minus the deference step for those segments
    # with fixed addresses
    def push_content_of_memory(mem_addr):
      return ASM(f'''
          // load memory address
          @{mem_addr}

          // save the value into D
          D=M

          $load_sp

          // write value to top of stack
          M=D

          $inc_sp
          ''')

    if segment in VM2ASM.SEGMENT_BASE_ADDR_TABLE:
      ptr_addr = VM2ASM.SEGMENT_BASE_ADDR_TABLE[segment]
      return push_content_of_ptr(ptr_addr, index)

    elif segment == 'temp':
      # b/c temp is fixed we can calculate the pointer address
      # directly
      mem_addr = VM2ASM.TEMP_BASE_ADDRESS + index
      return push_content_of_memory(mem_addr)

    elif segment == 'pointer':
      # set the addr of this (0) or that (1)
      ptr_name = ['this', 'that'][index]
      mem_addr = VM2ASM.SEGMENT_BASE_ADDR_TABLE[ptr_name]
      return push_content_of_memory(mem_addr)

    elif segment == 'constant':
      return ASM(f'''
          // load the constant into D
          @{index}
          D=A

          // load the stack pointer
          $load_sp

          // write the constant to the top
          // of the stack
          M=D

          $inc_sp
          ''')

    else:
      raise NameError(f'Unknown segment {segment}')


class POP_Operation(Operation):
  """
  POPs value at the top of the stack into segment[index]. SP
  is decremented.
  """
  def resolve(self, known_symbols=None):
    segment, index = self.args
    segment, index = Operation.validate_segment_index(segment, index, known_symbols)

    def pop_into_ptr(ptr_addr, offset):
      if offset == 0:
        return ASM(f'''
            $load_sp
            A=A-1

            // load top-of-stack value into D
            D=M

            // load the pointer value
            @{ptr_addr}

            // dereference the pointer
            A=M

            // write D into destination
            M=D

            $dec_sp
            ''')
      else:
        if self.compat:
          return ASM(f'''
              // load the pointer value into D
              @{ptr_addr}
              D=M

              // load the offset into A
              @{offset}

              // calculate the new pointer value
              // and save into D
              D=A+D

              // save the value into T0
              @T0
              M=D

              $load_sp
              A=A-1

              // load top-of-stack value into D
              D=M

              // load pointer value
              @T0

              // dereference the pointer
              A=M

              // write D into destination
              M=D

              $dec_sp
              ''')
        else:
          return ASM(f'''
              $load_sp
              A=A-1

              // load top-of-stack value into W
              W=M

              // load the pointer value into D
              @{ptr_addr}
              D=M

              // load the offset into A
              @{offset}

              // calculate the new pointer value
              // and dereference
              A=A+D

              // write W into destination
              M=W

              $dec_sp
              ''')

    # this is like pop_into_ptr but without the dereferencing step
    # for those segments with fixed base address.
    def pop_into_memory(mem_addr):
      return ASM(f'''
          $load_sp
          A=A-1

          // load top-of-stack value into D
          D=M

          // load the memory address
          @{mem_addr}

          // write D into destination
          M=D

          $dec_sp
          ''')

    if segment in VM2ASM.SEGMENT_BASE_ADDR_TABLE:
      ptr_addr = VM2ASM.SEGMENT_BASE_ADDR_TABLE[segment]
      return pop_into_ptr(ptr_addr, index)

    elif segment == 'temp':
      # b/c temp is fixed we can calculate the pointer address
      # directly
      mem_addr = VM2ASM.TEMP_BASE_ADDRESS + index
      return pop_into_memory(mem_addr)

    elif segment == 'pointer':
      # set the addr of this (0) or that (1)
      ptr_name = ['this', 'that'][index]
      mem_addr = VM2ASM.SEGMENT_BASE_ADDR_TABLE[ptr_name]
      return pop_into_memory(mem_addr)

    else:
      raise NameError(f'Unknown segment {segment}')


class LABEL_Operation(Operation):
  def resolve(self, known_symbols=None):
    # we don't use $ID_ macro here b/c these labels
    # originate from the user and could have scope beyond the
    # assembly emitted for this operation
    return ASM(f'({self._label_in_namespace})')

class GOTO_Operation(Operation):
  def resolve(self, known_symbols=None):
    # see comment in LABEL_Operation.resolve
    return ASM(f'''
        // load jump destination into A
        @{self._label_in_namespace}

        // unconditional jump
        0;JEQ
        ''')

class IFGOTO_Operation(Operation):
  def resolve(self, known_symbols=None):
    # see comment in LABEL_Operation.resolve
    return ASM(f'''
        $load_sp

        // pop value into D
        A=A-1
        D=M

        // we have to do this now b/c once
        // the jump executes it is too late
        $dec_sp

        // load jump destination
        @{self._label_in_namespace}

        // take a leaf from most languages: true
        // means !0
        D;JNE
        ''')


class FUNCTION_Operation(Operation):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    # do this avoid any possibility we are associated with
    # another function
    self.function_name = self.args[0]

  def resolve(self, known_symbols=None):
    # XXX STUB
    return ASM('')


#################
# HERE BE TESTS #
# ###############


def test_add():
  asm = ADD_Operation().resolve()
  print(asm)
  expected = ASM('''
      // MACRO=LOAD_SP
      @SP
      A=M
      // MACRO_END
      // pop y into D
      A=A-1
      D=M
      // pop x into M
      A=A-1
      // do the operation
      M=M+D
      // MACRO=DEC_SP
      @SP
      M=M-1
      // MACRO_END
        ''')
  assert str(asm) == str(expected)

  # make sure it output valid assembly
  assembler = Assembler()
  assembler.assemble(str(asm))

def test_sub():
  asm = SUB_Operation().resolve()
  Assembler().assemble(str(asm))

def test_and():
  asm = AND_Operation().resolve()
  Assembler().assemble(str(asm))

def test_or():
  asm = OR_Operation().resolve()
  Assembler().assemble(str(asm))

def test_neg():
  asm = NEG_Operation().resolve()
  Assembler().assemble(str(asm))

def test_not():
  asm = NOT_Operation().resolve()
  Assembler().assemble(str(asm))

def test_eq():
  asm = EQ_Operation().resolve()
  Assembler().assemble(str(asm))

def test_neq():
  asm = NEQ_Operation().resolve()
  Assembler().assemble(str(asm))

def test_lt():
  asm = LT_Operation().resolve()
  Assembler().assemble(str(asm))

def test_lte():
  asm = LTE_Operation().resolve()
  Assembler().assemble(str(asm))

def test_gt():
  asm = GT_Operation().resolve()
  Assembler().assemble(str(asm))

def test_gte():
  asm = GTE_Operation().resolve()
  print(asm)
  Assembler().assemble(str(asm))

def test_push():
  asm = PUSH_Operation(['constant', '255']).resolve()
  print(asm.to_string(comments=False))
  Assembler().assemble(str(asm))

def test_unique_labels():
  asm1 = ASM('$_LABEL')

  # we should generate unique asm every time
  assert str(asm1) != str(asm1)

def test_segment_setup():
  translator = VM2ASM(None, LCL=300, ARG=400, THIS=3000, THAT=3010)
  Assembler().assemble(translator.dumps())

def test_push_argument():
  translator = VM2ASM(None, LCL=300, ARG=400, THIS=3000, THAT=3010, annotate=True)
  translator.translate('push argument 2')
  asm = translator.dumps()
  Assembler().assemble(asm)

def test_push_local():
  translator = VM2ASM(None, LCL=300, ARG=400, THIS=3000, THAT=3010, annotate=True)
  translator.translate('push local 1')
  asm = translator.dumps()
  Assembler().assemble(asm)

def test_push_this():
  translator = VM2ASM(None, LCL=300, ARG=400, THIS=3000, THAT=3010, annotate=True)
  translator.translate('push this 1')
  asm = translator.dumps()
  Assembler().assemble(asm)

def test_push_that():
  translator = VM2ASM(None, LCL=300, ARG=400, THIS=3000, THAT=3010, annotate=True)
  translator.translate('push that 1')
  asm = translator.dumps()
  Assembler().assemble(asm)

def test_push_pointer():
  translator = VM2ASM(None, LCL=300, ARG=400, THIS=3000, THAT=3010, annotate=True)
  translator.translate('push that 1')
  asm = translator.dumps()
  Assembler().assemble(asm)

def test_push_static():
  translator = VM2ASM(None, annotate=True)
  translator.translate('push static 1')
  asm = translator.dumps()
  Assembler().assemble(asm)

def test_push_temp():
  translator = VM2ASM(None, annotate=True)
  translator.translate('push temp 1')
  asm = translator.dumps()
  Assembler().assemble(asm)

def test_segment_index_validation():
  try:
    translator = VM2ASM(None, annotate=True)
    translator.translate('push temp 10')
    assert 'Should have failed'
  except ValueError:
    pass

def test_compat():
  asm = EQ_Operation(compat=True).resolve()
  Assembler(compat=True).assemble(str(asm))

  try:
    asm = EQ_Operation().resolve()
    Assembler(compat=True).assemble(str(asm))
  except:
    pass
  else:
    assert False, 'Should have failed'

def test_pop_compat():
  translator = VM2ASM(LCL=300, ARG=400, THIS=3000, THAT=3010, annotate=True, compat=True)
  asm = translator.translate('pop argument 1').dumps()
  Assembler().assemble(asm)
  print(asm)

def test_pop_argument():
  translator = VM2ASM(LCL=300, ARG=400, THIS=3000, THAT=3010, annotate=True)
  asm = translator.translate('pop argument 1').dumps()
  Assembler().assemble(asm)

def test_pop_local():
  translator = VM2ASM(LCL=300, ARG=400, THIS=3000, THAT=3010, annotate=True)
  asm = translator.translate('pop local 1').dumps()
  Assembler().assemble(asm)

def test_pop_static():
  translator = VM2ASM(LCL=300, ARG=400, THIS=3000, THAT=3010, annotate=True)
  asm = translator.translate('pop static 1').dumps()
  Assembler().assemble(asm)

def test_pop_pointer():
  translator = VM2ASM(LCL=300, ARG=400, THIS=3000, THAT=3010, annotate=True)
  asm = translator.translate('pop pointer 1').dumps()
  Assembler().assemble(asm)

def test_pop_this():
  translator = VM2ASM(LCL=300, ARG=400, THIS=3000, THAT=3010, annotate=True)
  asm = translator.translate('pop this 1').dumps()
  Assembler().assemble(asm)

def test_pop_that():
  translator = VM2ASM(LCL=300, ARG=400, THIS=3000, THAT=3010, annotate=True)
  asm = translator.translate('pop that 1').dumps()
  Assembler().assemble(asm)

def test_pop_temp():
  translator = VM2ASM(LCL=300, ARG=400, THIS=3000, THAT=3010, annotate=True)
  asm = translator.translate('pop temp 1').dumps()
  Assembler().assemble(asm)

def test_label():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('label HELLO').dumps().strip()
  assert asm == '(HELLO)'
  Assembler().assemble(asm)

def test_label_in_function():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('''
      function HELLO 0
      label WORLD
  ''').dumps()
  assert 'HELLO:WORLD' in asm
  Assembler().assemble(asm)

def test_goto():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('''
      label abc
      goto abc
  ''').dumps()
  Assembler().assemble(asm)

def test_ifgoto():
  translator = VM2ASM(no_init=True, annotate=True)
  asm = translator.translate('''
      label abc
      push constant 1
      if-goto abc
  ''').dumps()
  Assembler().assemble(asm)
  print(asm)

def test_push_defined_constant():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('push constant $SCREEN').dumps()
  Assembler().assemble(asm)
  print(asm)

if __name__ == '__main__':
  main()
