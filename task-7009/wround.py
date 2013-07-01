#!/usr/bin/python
import sys
import re
import os
def wround(v):
    if v < 8:
       return 8
    elif v < 128:
       downto = 1
    elif v < 1024:
       downto = 3
    else:
       downto = 7 
    v_orig = v
    shift = 0
    while v > downto:
       v >>= 1
       shift += 1
    return v << shift

p = re.compile(r'w Bandwidth=(\d+)(.*)')

def rewrite(fname):
   inp = open(fname)
   out = open(fname+".tmp", 'w')
   for line in inp:
       m = p.match(line)
       if not m:
          out.write(line)
          continue
       v = wround(int(m.group(1)))
       out.write("w Bandwidth=%s%s\n"%(v,m.group(2).rstrip()))
   out.close()
   inp.close()
   os.rename(fname+".tmp", fname) 

for fn in sys.argv[1:]:
    rewrite(fn)

