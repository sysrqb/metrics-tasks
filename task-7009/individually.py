#!/usr/bin/python

import os
import sys
import subprocess

def uncompressed(fname):
	return os.stat(fname).st_size

def gz(fname):
	try:
		os.unlink("out.tmp")
	except OSError, e:
		pass
	os.system("gzip -c -9 %s > out.tmp" % fname)
	return os.stat("out.tmp").st_size 

def bz2(fname):
	os.unlink("out.tmp")
	os.system("bzip2 -c -9 %s > out.tmp" % fname)
	return os.stat("out.tmp").st_size 

def xz(fname):	
	os.unlink("out.tmp")
	os.system("xz -c -9 %s > out.tmp" %fname)
	return os.stat("out.tmp").st_size 

func = globals()[sys.argv[1]]

allvals = []
total = 0L
N = 0

for fname in sys.argv[2:]:
	n = func(fname)
	N += 1
	total += n
	allvals.append(n)

allvals.sort()
print "%s: mean %s. median %s"%(sys.argv[1], total//N, allvals[N//2])

	
