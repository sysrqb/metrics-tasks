#!/usr/bin/python
import sys

class Router:
    def __init__(self, r_line):
        assert r_line.startswith("r ")
        self.ident = r_line.split()[2]
        self.lines = [ r_line ]
    def append(self, line):
        self.lines.append(line)


def rdiff(r1,r2):
    r1 = r1.split()
    r2 = r2.split()
    p1 = ["r"]
    p2 = []
    for i in xrange(len(r1)):
       if r1[i] == r2[i]:
           continue
       p1.append(str(i))
       p2.append(r2[i])
    return "".join(p1) + " " + " ".join(p2)

def sdiff(s1, s2):
    s1 = set(s1.split()[1:])
    s2 = set(s2.split()[1:])
    minus = sorted(("-%s"%item) for item in s1 if item not in s2)
    plus = sorted(("+%s"%item) for item in s2 if item not in s1)
    return " ".join(["s"] + minus + plus)  

def splitfile(f):
    header, body, footer = [], [], []
    inHeader = True
    inBody = False
    inFooter = False
    for line in f.readlines():
        if inHeader and line.startswith("r "):
            inBody = True
            inHeader = False
            curRouter = None
        if inBody and line.startswith("directory-footer"):
            inFooter = True
            inBody = False

        if inHeader:
            header.append(line)

        if inBody:
            if line.startswith("r "):
                curRouter = Router(line)
                body.append(curRouter)
            else:
                curRouter.append(line)

        if inFooter:
            footer.append(line)

    assert inFooter
    return header, body, footer


def main(f1, f2):
    _, body1, _ = splitfile(f1)
    header2, body2, footer2 = splitfile(f2)
    assert footer2

    for h in header2:
        sys.stdout.write(h)

    while body1 and body2:
        if body1[0].ident < body2[0].ident:
            print "-"
            del body1[0]
        elif body1[0].ident > body2[0].ident:
            sys.stdout.write("* ")
            for b in body2[0].lines:
                sys.stdout.write(b)
            del body2[0]
        else: # same router
            if body1[0].lines != body2[0].lines:
                if len(body1[0].lines) != len(body2[0].lines):
                    print >>sys.stderr, "<<%s>><<%s>>"%(body1[0].lines, body2[0].lines)
                    sys.stdout.write("** ")
                    for b in body2[0].lines:
                        sys.stdout.write(b)
                    del body2[0]
                    del body1[0]
                    continue

                if body1[0].lines[0] == body2[0].lines[0]:
                    print "."
                else:
                    print rdiff(body1[0].lines[0],body2[0].lines[0])
                for l1,l2 in zip(body1[0].lines[1:], body2[0].lines[1:]):
                    if l1 != l2:
                       if l2.startswith('s ') and l1.startswith('s '):
                           print  sdiff(l1, l2)
                       else:
                           sys.stdout.write(l2)
	    del body1[0]
            del body2[0]

    for r in body2:
        sys.stdout.write("* ")
        for l in r.lines:
           sys.stdout.write(l)

    for f in footer2:
        sys.stdout.write(f)

f1 = open(sys.argv[1])
f2 = open(sys.argv[2])

main(f1,f2)
