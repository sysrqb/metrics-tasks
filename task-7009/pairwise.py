#!/usr/bin/python

import os
import sys
import subprocess

def echo(a,b):
	print a, b
	return 0

def diff_gz(fn, fn2):
	os.unlink("out.tmp")
	os.system("diff %s %s | gzip -9 -c > out.tmp" % (fn, fn2))
	return os.stat("out.tmp").st_size 
def diff_u_gz(fn, fn2):
	os.unlink("out.tmp")
	os.system("diff -u %s %s | gzip -9 -c > out.tmp" % (fn, fn2))
	return os.stat("out.tmp").st_size 
def diff_e_gz(fn, fn2):
	os.unlink("out.tmp")
	os.system("diff -e %s %s | gzip -9 -c > out.tmp" % (fn, fn2))
	return os.stat("out.tmp").st_size 

def diff_bz2(fn, fn2):
	os.unlink("out.tmp")
	os.system("diff %s %s | bzip2 -9 -c > out.tmp" % (fn, fn2))
	return os.stat("out.tmp").st_size 
def diff_u_bz2(fn, fn2):
	os.unlink("out.tmp")
	os.system("diff -u %s %s | bzip2 -9 -c > out.tmp" % (fn, fn2))
	return os.stat("out.tmp").st_size 
def diff_e_bz2(fn, fn2):
	os.unlink("out.tmp")
	os.system("diff -e %s %s | bzip2 -9 -c > out.tmp" % (fn, fn2))
	return os.stat("out.tmp").st_size 

def condiff_gz(fn, fn2):
	os.unlink("out.tmp")
	os.system("./condiff.py %s %s | gzip -9 -c > out.tmp" % (fn, fn2))
	return os.stat("out.tmp").st_size 
def condiff_bz2(fn, fn2):
	os.unlink("out.tmp")
	os.system("./condiff.py %s %s | bzip2 -9 -c > out.tmp" % (fn, fn2))
	return os.stat("out.tmp").st_size 

def condiff2_gz(fn, fn2):
	os.unlink("out.tmp")
	os.system("./condiff2.py %s %s | gzip -9 -c > out.tmp" % (fn, fn2))
	return os.stat("out.tmp").st_size 
def condiff2_bz2(fn, fn2):
	os.unlink("out.tmp")
	os.system("./condiff2.py %s %s | bzip2 -9 -c > out.tmp" % (fn, fn2))
	return os.stat("out.tmp").st_size 

f = open("out.tmp", 'w')
f.write("xyz")
f.close()

func = globals()[sys.argv[1]]

allvals = []
total = 0L
N = 0

lag = int(sys.argv[2])

def pairwise(it):
	it = iter(it)
	lastv = []
	for i in xrange(lag):
		lastv.append(it.next())
	for v in it:
		yield lastv[0], v
		lastv.append(v)
		del lastv[0]

for fname, fname2 in pairwise(sys.argv[3:]):
	n = func(fname, fname2)
	N += 1
	total += n
	allvals.append(n)

allvals.sort()
print "%s: lag %s: mean %s. median %s"%(sys.argv[1], lag, total//N, allvals[N//2])

	
