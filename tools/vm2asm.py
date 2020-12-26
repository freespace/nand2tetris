#!/usr/bin/env python3

"""
N.B. when adding new instructions avoid direct manipulation of @SP. Use the sp macros, e.g.
$load_sp, etc. This allows us to easily emit optimised assembly when running on the HACKx
platform which uses the W register for SP
"""

import click

from assembler import Assembler
from asm import ASM

NAMESPACE_FILE = 'file'
NAMESPACE_FUNCTION = 'function'

@click.command()
@click.argument('input_vm_files', nargs=-1, type=click.Path(dir_okay=False, exists=True))
@click.option('-o', '--output-asm-file', type=click.Path(dir_okay=False),
              help='Output asm file')
@click.option('-C', '--compat', is_flag=True,
              help='If runs in compatibility mode in which the output is '
                   'exactly produced by the reference translator written in '
                   'java')
@click.option('-A', '--annotate', is_flag=True,
              help='If given hack output will be annotated with source '
                   'lines or PC counts')
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
              help='If given no initialisation code is generated, which means no SP initalisation'
                   'and no call to the init function')
@click.option('--init-function', type=str, default='Sys.init',
              help='When compiling multiple files into a single assembly unit this specifies'
                   'the name of the function to call after initialisation. Defaults to'
                   'Sys.init as per course specifications')
def main(input_vm_files, *args, **kwargs):

  init_function_name = kwargs.pop('init_function')
  output_file = kwargs.pop('output_asm_file')

  if kwargs['no_init']:
    output_asm = ''
  else:
    # generate init code
    translator = VM2ASM(*args, **kwargs)
    translator.translate(f'call {init_function_name} 0')
    output_asm = translator.dumps() + '\n\n'

  # all sub-translation units do no initialisation
  kwargs['no_init'] = True

  for vm_file in input_vm_files:
    kwargs['input_vm'] = vm_file
    translator = VM2ASM(*args, **kwargs)
    translator.translate()

    output_asm += translator.dumps()
    output_asm += '\n\n'

  if output_file is not None:
    with open(output_file, 'w') as fh:
      fh.write(output_asm)
  else:
    print(output_asm)

class VM2ASM:
  """
  In non-compat mode we dedicate the W register to storing SP
  """
  STATIC_BASE_ADDRESS = 16
  STACK_BASE_ADDRESS = 256
  HEAP_BASE_ADDRESS = 16483
  TEMP_BASE_ADDRESS = 5

  SEGMENT_BASE_ADDR_TABLE = {
      'argument': 'ARG',
      'local'   : 'LCL',
      'this'    : 'THIS',
      'that'    : 'THAT',
  }

  SEGMENT_SIZE_TABLE = {
      'static'  : 255 - STATIC_BASE_ADDRESS + 1,
      'temp'    : 8,
      'pointer' : 2,
  }

  PREDEFINED_CONSTANTS = {
      '$SCREEN': Assembler.PREDEFINED_LABELS['SCREEN'],
  }

  def __init__(self,
               input_vm=None,
               compat=False,
               annotate=False,
               no_init=False,
               ram_specs=None,
               LCL=None,
               ARG=None,
               THIS=None,
               THAT=None):
    self._input_vm = input_vm
    self._compat = compat
    self._annotate = annotate
    self._known_symbols = dict(VM2ASM.PREDEFINED_CONSTANTS)
    self._operations = None

    ASM.set_compat(self._compat)

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

      self.asm_output.append('// INIT BEGIN')

      set_ram('SP', VM2ASM.STACK_BASE_ADDRESS)

      if not self._compat:
        asm = ASM('''
            // setup the W register as SP replacement
            @{VM2ASM.STACK_BASE_ADDRESS}
            W=A
            ''')
        self.asm_output += asm.to_list(indent=4)

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

      # set all temp variables to 0
      set_ram('T0', 0)
      set_ram('T1', 0)
      set_ram('T2', 0)

      if annotate:
        self.asm_output.append('// INIT END')

  def write_asm(self, output_file):
    with open(output_file, 'w') as fh:
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

    if self._input_vm is not None:
      filename = self._input_vm
    else:
      filename = '<in memory>'
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
      op = self._parse(l, current_function_name, filename)
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

  def _parse(self, source_line, current_function_name, filename):
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

      # memory management
      'push': PUSH_Operation,
      'pop' : POP_Operation,

      # program flow
      'label'  : LABEL_Operation,
      'goto'   : GOTO_Operation,
      'if-goto': IFGOTO_Operation,

      # function calling
      'function': FUNCTION_Operation,
      'call': CALL_Operation,
      'return': RETURN_Operation,

      # EXTENSIONS
      # extra equality checks
      'neq': NEQ_Operation,
      'lte': LTE_Operation,
      'gte': GTE_Operation,

      # direct segment manipulation
      's_neg'  : S_NEG_Operation,
      's_not'  : S_NOT_Operation,
      's_dec'  : S_DEC_Operation,
      's_inc'  : S_INC_Operation,
      's_clear': S_CLEAR_Operation,
      's_set'  : S_SET_Operation,
    }

    try:
      op_cls = operation_table[op]
    except KeyError:
      raise SyntaxError(f'Unknown operation {op}')

    return op_cls(args,
                  compat=self._compat,
                  function_name=current_function_name,
                  filename=filename)

class Operation:
  """
  See note at top of file re: adding new instructions.

  The namespace argument controls how we generate labels. Normally labels inside functions are
  prefixed using the function's name to avoid label collisions, e.g. function FOO and BAR can
  both use WHILE as a label without issue b/c the generated labels are FOO.WHILE and BAR.WHILE
  respectively. However some labels, such as those for static variables are file-scope, so
  they need to be generated using the filename as the prefix.

  :param args: array of arguments, i.e. everything that comes after the operation name, separated
         by space. e.g. 'abc 123' => ['abc', '123']
  :param compat: when True generates HACK compatible asm, otherwise generates HACKx compatible
         asm. Default is False.
  :param function_name: name of the function this operation is in, None if not known (Default).
  :param filename: name of the file this operation is in, None if not known (Default).
  :param namespace: namespace of this operation, defaults to 'function', can also be 'file'
  :return: instance of Operation

  """
  def __init__(self, args=None, compat=False, function_name=None, filename=None, namespace='function'):
    self.args = args
    self.compat = compat
    self.function_name = function_name
    self.filename = filename
    self.label_suffix = None
    self.namespace = namespace

  @staticmethod
  def validate_segment_index(segment, index, known_symbols):
    try:
      if index[0] == '$':
        # try to resolve the constant
        index = known_symbols[index]
    except KeyError:
      raise NameError(f'Unknown constant {index}')

    try:
      index = int(index)
    except ValueError:
      raise ValueError(f'Invalid index value {index}')

    if segment in VM2ASM.SEGMENT_SIZE_TABLE:
      if index >= VM2ASM.SEGMENT_SIZE_TABLE[segment]:
        raise ValueError(f'{index} out of range for segment {segment}')

    return segment, index

  @property
  def label_in_namespace(self):
    label = self.args[0]

    if self.namespace == NAMESPACE_FUNCTION:
      if self.function_name is not None and not isinstance(self, FUNCTION_Operation):
        label = f'{self.function_name}::{label}'

    if self.namespace == NAMESPACE_FILE:
      if self.filename is not None:
        label = f'{self.filename}::{label}'

    if self.label_suffix is not None:
      label = f'{label}:{self.label_suffix}'

    # sanitise the label
    safe_label = []
    for c in label:
      if c.isalnum() or c in '._:':
        safe_label.append(c)
      else:
        safe_label.append('_')

    if safe_label[0].isdigit():
      raise Exception('Label cannot start with a digit')

    return ''.join(safe_label)

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

        $load_sp
        A=A-1

        // write 0
        M=0

        ($_END)
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
    self.namespace = NAMESPACE_FILE

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

    elif segment == 'static':
      # static is special where we don't actually index into anything but auto-allocate into
      # the variable memory address. We leave that job to the assembler
      mem_addr = f'{self.label_in_namespace}.STATIC{index}'
      return push_content_of_memory(mem_addr)

    elif segment == 'pointer':
      # set the addr of this (0) or that (1)
      ptr_name = ['this', 'that'][index]
      mem_addr = VM2ASM.SEGMENT_BASE_ADDR_TABLE[ptr_name]
      return push_content_of_memory(mem_addr)

    elif segment == 'constant':
      return ASM(f'''
          // load {index} into D
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
    self.namespace = NAMESPACE_FILE

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

    elif segment == 'static':
      # static is special where we don't actually index into anything but auto-allocate into
      # the variable memory address. We leave that job to the assembler
      mem_addr = f'{self.label_in_namespace}.STATIC{index}'
      return pop_into_memory(mem_addr)

    elif segment == 'pointer':
      # set the addr of this (0) or that (1)
      ptr_name = ['this', 'that'][index]
      mem_addr = VM2ASM.SEGMENT_BASE_ADDR_TABLE[ptr_name]
      return pop_into_memory(mem_addr)

    else:
      raise NameError(f'Unknown segment {segment}')

class S_Operation(Operation):
  def resolve(self, known_symbols=None):
    segment, index = self.args
    segment, index = Operation.validate_segment_index(segment, index, known_symbols)

    def operate_on_content_of_ptr(ptr_addr, offset):
      if offset == 0:
        return ASM(f'''
            // load the pointer value
            @{ptr_addr}

            // dereference the pointer
            A=M

            // operate on content-of pointer
            M=%COMP%
            ''')
      else:
        return ASM(f'''
            // load the pointer value into D
            @{ptr_addr}
            D=M

            // load the offset into A
            @{offset}

            // calculate the new pointer value
            // and save into D
            A=A+D

            // dereference the pointer
            A=M

            // operate on content-of pointer
            M=%COMP%
            ''')

    # this is like operate_on_content_of_ptr but without the dereferencing step
    # for those segments with fixed base address.
    def operate_on_memory(mem_addr):
      return ASM(f'''
          // load the memory address
          @{mem_addr}

          // write D into destination
          M=%COMP%
          ''')

    if segment in VM2ASM.SEGMENT_BASE_ADDR_TABLE:
      ptr_addr = VM2ASM.SEGMENT_BASE_ADDR_TABLE[segment]
      return operate_on_content_of_ptr(ptr_addr, index)

    elif segment == 'temp':
      # b/c temp is fixed we can calculate the pointer address
      # directly
      mem_addr = VM2ASM.TEMP_BASE_ADDRESS + index
      return operate_on_memory(mem_addr)

    elif segment == 'pointer':
      # set the addr of this (0) or that (1)
      ptr_name = ['this', 'that'][index]
      mem_addr = VM2ASM.SEGMENT_BASE_ADDR_TABLE[ptr_name]
      return operate_on_memory(mem_addr)

    else:
      raise NameError(f'Unknown segment {segment}')


class S_NOT_Operation(S_Operation):
  def resolve(self, *args, **kwargs):
    return super().resolve(*args, **kwargs).replace('%COMP%', '!M')


class S_NEG_Operation(S_Operation):
  def resolve(self, *args, **kwargs):
    return super().resolve(*args, **kwargs).replace('%COMP%', '-M')


class S_INC_Operation(S_Operation):
  def resolve(self, *args, **kwargs):
    return super().resolve(*args, **kwargs).replace('%COMP%', 'M+1')


class S_DEC_Operation(S_Operation):
  def resolve(self, *args, **kwargs):
    return super().resolve(*args, **kwargs).replace('%COMP%', 'M-1')


class S_SET_Operation(S_Operation):
  def resolve(self, *args, **kwargs):
    return super().resolve(*args, **kwargs).replace('%COMP%', '-1')


class S_CLEAR_Operation(S_Operation):
  def resolve(self, *args, **kwargs):
    return super().resolve(*args, **kwargs).replace('%COMP%', '0')


class LABEL_Operation(Operation):
  def resolve(self, known_symbols=None):
    # we don't use $ID_ macro here b/c these labels
    # originate from the user and could have scope beyond the
    # assembly emitted for this operation
    return ASM(f'({self.label_in_namespace})')

class GOTO_Operation(Operation):
  def resolve(self, known_symbols=None):
    # see comment in LABEL_Operation.resolve
    return ASM(f'''
        // load jump destination into A
        @{self.label_in_namespace}

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
        @{self.label_in_namespace}

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
    if int(self.args[1]) > 0:
      function_init = f'''
        ({self.label_in_namespace})
        $load_sp
      '''

      local_init = '''
        // set the current top of stack to 0
        M=0

        // increment top of stack
        A=A+1
      '''*int(self.args[1])

      sp_prep = '''
        // need this so SP now points to the next available
        // slot after local vars
        $save_sp
      '''
      return ASM(function_init + local_init + sp_prep)
    else:
      # when we use no local vars we don't need any init, just a label
      return ASM(f'''
        ({self.label_in_namespace})
      ''')

class CALL_Operation(Operation):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    # we are exploiting the fact both the call and function operations have the function name
    # as the first argument
    self.f_op = FUNCTION_Operation(*args, **kwargs)
    self.label_suffix = 'RETURN_FROM_CALL'

  def resolve(self, known_symbols=None):
    """
    Note that we use the $_ macro to ensure a unique label b/c self.label_in_namespace is the same
    for calls to the same function in the same file
    """
    return ASM(f'''
      // push return addr onto the stack
      // load the return addr into D via A
      @$_{self.label_in_namespace}
      D=A
      $load_sp
      M=D
      $inc_sp

      // push LCL onto the stack
      // point M to LCL
      @LCL
      D=M
      $load_sp
      M=D
      $inc_sp

      // push ARG onto the stack
      @ARG
      D=M
      $load_sp
      M=D
      $inc_sp

      // push THIS onto the stack
      @THIS
      D=M
      $load_sp
      M=D
      $inc_sp

      // push THAT onto the stack
      @THAT
      D=M
      $load_sp
      M=D
      $inc_sp

      // recalculate ARG: ARG = SP - n - 5
      // note that to be backward compat  with HACK platform we can't manipulate the W
      // register directly

      // SP - n
      @{self.args[1]}
      D=A
      $load_sp
      // use D for destination b/c we are about to use A for a constant
      D=A-D

      // ... -5
      @5
      D=D-A

      // D now contains the new ARG value which we need to save into the ARG register
      @ARG
      M=D

      // write current SP into LCL register
      $load_sp
      D=A
      @LCL
      M=D

      // jump to the function entry point
      @{self.f_op.label_in_namespace}
      0;JEQ

      ($_{self.label_in_namespace})
  ''')

class RETURN_Operation(Operation):
  def resolve(self, known_symbols=None):
    return ASM('''
      // save the return address at LCL-5 into FRAME b/c we will be updating LCL soon and also
      // if number of arguments is 0 ARG and LCL-5 are pointing to the same place and we will
      // end up overwriting the return address when we store the return value into ARG
      @5
      D=A
      @LCL
      A=M-D
      D=M
      @RET
      M=D

      // store the return value where ARG is pointing to, i.e. *ARG=*SP
      $load_sp
      A=A-1
      D=M
      @ARG
      A=M
      M=D

      // set A to 1 past ARG and save as SP
      @ARG
      A=M+1
      $save_sp

      // restore THAT at LCL-1
      @LCL
      A=M-1
      D=M
      @THAT
      M=D

      // restore THIS at LCL-2
      @2
      D=A
      @LCL
      A=M-D
      D=M
      @THIS
      M=D

      // restore ARG at LCL-3
      @3
      D=A
      @LCL
      A=M-D
      D=M
      @ARG
      M=D

      // restore LCL at LCL-4
      @4
      D=A
      @LCL
      A=M-D
      D=M
      @LCL
      M=D

      // load *RET into A and do an unconditional jump to that address
      @RET
      A=M
      0;JEQ
    ''')

#################
# HERE BE TESTS #
# ###############

# most of these tests are not true tests but more a way to (a) excercise the function
# and (b) make sure it at least runs and assembles
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
  translator = VM2ASM(None, annotate=True, no_init=True)
  translator.translate('push static 1')
  asm = translator.dumps()
  Assembler().assemble(asm)
  print(asm)

  translator = VM2ASM(None, annotate=True, no_init=True)
  translator.translate('''
    function foo 0
    push static 1
    return
  ''')
  asm = translator.dumps()
  Assembler().assemble(asm)
  print(asm)

def test_push_temp():
  translator = VM2ASM(None, annotate=True)
  translator.translate('push temp 1')
  asm = translator.dumps()
  Assembler().assemble(asm)

def test_segment_index_validation():
  try:
    translator = VM2ASM(None, annotate=True)
    translator.translate('push temp 10')
    assert False, 'Should have failed'
  except ValueError:
    pass

def test_compat():
  ASM.set_compat(True)
  asm = EQ_Operation(compat=True).resolve()
  Assembler(compat=True).assemble(str(asm))

  try:
    ASM.set_compat(False)
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
  translator = VM2ASM(annotate=True, no_init=True)
  asm = translator.translate('pop static 1').dumps()
  Assembler().assemble(asm)
  print('pop static 1\n', asm)

  translator = VM2ASM(annotate=True, no_init=True)
  asm = translator.translate('pop static 0').dumps()
  Assembler().assemble(asm)
  print('pop static 0\n', asm)

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
  assert asm == '(_in_memory_.HELLO)'
  Assembler().assemble(asm)

def test_label_in_function():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('''
      function HELLO 0
      label WORLD
  ''').dumps()
  assert '_in_memory_.HELLO.WORLD' in asm
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

def test_pop_optimisation():
  translator = VM2ASM(no_init=True)
  asm1 = translator.translate('pop this 0').dumps()
  translator = VM2ASM(no_init=True)
  asm2 = translator.translate('pop this 1').dumps()

  assert len(asm1) < len(asm2)

def test_push_optimisation():
  translator = VM2ASM(no_init=True)
  asm1 = translator.translate('push this 0').dumps()
  translator = VM2ASM(no_init=True)
  asm2 = translator.translate('push this 1').dumps()

  assert len(asm1) < len(asm2)

def test_s_neg():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('s_neg temp 0').dumps()
  Assembler().assemble(asm)
  asm = translator.translate('s_neg local 1').dumps()
  Assembler().assemble(asm)

def test_s_not():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('s_not temp 0').dumps()
  Assembler().assemble(asm)
  asm = translator.translate('s_not local 1').dumps()
  Assembler().assemble(asm)

def test_s_inc():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('s_inc temp 0').dumps()
  Assembler().assemble(asm)
  asm = translator.translate('s_inc local 1').dumps()
  Assembler().assemble(asm)

def test_s_dec():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('s_dec temp 0').dumps()
  Assembler().assemble(asm)
  asm = translator.translate('s_dec local 1').dumps()
  Assembler().assemble(asm)

def test_s_set():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('s_set temp 0').dumps()
  Assembler().assemble(asm)
  asm = translator.translate('s_set local 1').dumps()
  Assembler().assemble(asm)

def test_s_clear():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('s_clear temp 0').dumps()
  Assembler().assemble(asm)
  asm = translator.translate('s_clear local 1').dumps()
  Assembler().assemble(asm)

def test_function():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('function FOO 5').dumps()
  Assembler().assemble(asm)
  print(asm)

def test_call():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('''
      function FOO 3
      call FOO 3
  ''').dumps()
  Assembler().assemble(asm)
  print(asm)

def test_return():
  translator = VM2ASM(no_init=True)
  asm = translator.translate('''
      function FOO 0
      push argument 0
      push argument 1
      sub
      return
  ''').dumps()
  Assembler().assemble(asm)
  print(asm)

if __name__ == '__main__':
  main()
