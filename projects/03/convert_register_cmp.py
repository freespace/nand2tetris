#!/usr/bin/env python

with open("Register.cmp") as fh:
  for num, l in enumerate(fh.readlines()):
    if num == 0:
      continue

    parts = [p.strip() for p in l.split('|')][2:]
    parts = [p for p in parts if len(p)]

    outparts = []
    # last element is always empty
    cols = ['in', 'load', 'out']
    for idx, p in enumerate(parts):
      c = cols[idx]
      v = int(p)&0xFFFF
      if c in ['in', 'out']:
        outparts.append(format(v, '016b'))
      else:
        outparts.append(format(v, 'b'))

    outstr = '_'.join(outparts)

    print(outstr)

    # duplicate the first so every time step has a t and t+
    if num == 1:
      print(outstr)

# print the last line again b/c it is missing its t+ line
print(outstr)
