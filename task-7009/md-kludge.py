#!/usr/bin/python

import sys
import re
import os

def read_table(fn):
  p = re.compile(r'^([^ ]*) sha256=([^ \n]*)')
  bad = 0
  t = {}
  for line in open(fn):
      m = p.match(line)
      if not m:
         bad += 1
         continue
      t[m.group(1)] = m.group(2)
  print bad, "bad entries in", fn
  return t


def process(fn, t):
   tmp = fn+".tmp"
   inp = open(fn, 'r')
   out = open(tmp, 'w')
   h = m = 0
   for line in inp:
      if line.startswith('r '):
          r = line.split()
          desc_id = r[3]
          del r[3]
          print >>out, " ".join(r)
          try:
             md_id = t[desc_id]
             h += 1
          except KeyError:
             md_id = desc_id #kluuuuuuuuudge!!!!!
             m += 1 
          print >>out, "m",md_id 
      else:
         out.write(line)
   inp.close()
   out.close()
   os.rename(tmp, fn)
   return h, m

table = read_table("table.txt")

hit = 0
miss = 0

for fn in sys.argv[1:]:
  h,m = process(fn, table)
  hit += h
  miss += m

print hit, miss
