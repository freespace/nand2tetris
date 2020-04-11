#!/usr/bin/env python

from random import randint

def gate(a, b):
  return a and b

for _ in range(16):
  a = [0]*16
  a[randint(0, 15)] = 1
  a[randint(0, 15)] = 1
  a[randint(0, 15)] = 1
  a[randint(0, 15)] = 1

  b = [0]*16
  b[randint(0, 15)] = 1
  b[randint(0, 15)] = 1
  b[randint(0, 15)] = 1
  b[randint(0, 15)] = 1

  out = [gate(x, y) for x, y in zip(a, b)]

  astr = '_'.join([str(x) for x in a])
  bstr = '_'.join([str(x) for x in b])
  ostr = '_'.join([str(x) for x in out])

  pipe = '|'
  print(f'//{pipe:>30s}{pipe:>32s}{pipe:>32s}')
  print(f'{astr}_{bstr}_{ostr}')
