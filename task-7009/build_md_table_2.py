#!/usr/bin/python
import sys

result = {}

for fname in sys.argv[1:]:
   f = open(fname, 'r')
   for line in f:
      if line.startswith('r '):
          lastR = line
      if line.startswith('m 8') or (line.startswith('m ') and ",8" in line):
          sha = line.split()[2]
          assert sha.startswith("sha256=")
          descID = lastR.split()[3]
	  result[descID] = sha
   f.close()
  
for k,v in result.iteritems():
   print k,v

