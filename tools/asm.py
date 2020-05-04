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

  MACRO_LOAD_WSP='''A=W'''
  MACRO_SAVE_WSP='''W=A'''
  MACRO_DEC_WSP='''W=W-1'''
  MACRO_INC_WSP='''W=W+1'''

  # must call set_compat before attempting resolve
  # instructions
  MACROS ={}

  ID_CNT = 0

  @classmethod
  def set_compat(cls, compat):
    if compat:
      cls.MACROS = {
          '$load_sp': cls.MACRO_LOAD_SP,
          '$save_sp': cls.MACRO_SAVE_SP,
          '$dec_sp' : cls.MACRO_DEC_SP,
          '$inc_sp' : cls.MACRO_INC_SP,
        }
    else:
      cls.MACROS = {
          '$load_sp': cls.MACRO_LOAD_WSP,
          '$save_sp': cls.MACRO_SAVE_WSP,
          '$dec_sp' : cls.MACRO_DEC_WSP,
          '$inc_sp' : cls.MACRO_INC_WSP,
        }

  def __init__(self, asm_text):
    assert len(ASM.MACROS) != 0, 'Must call ASM.set_compat() first'
    self._text = asm_text

  def replace(self, target, replacement):
    self._text = self._text.replace(target, replacement)

  def to_list(self, indent=0, comments=True):
    # this ensures if the instruction is reused it still
    # emits different IDs
    macros = dict(ASM.MACROS)
    macros['$_'] = f'__{ASM.ID_CNT}__'
    ASM.ID_CNT += 1

    txt = self._text

    # insert macros
    for macro_name, macro_asm in macros.items():
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

# default to compat mode
ASM.set_compat(True)

