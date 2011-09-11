## file makefile
##

## $Id$
## Copyright 1997-1999, D J Moore

## $Log$
##


## make variables

SRCDIR=$(HOME)/play
LIBDIR=$(HOME)/play/lib
VPATH=
HDRS=-I$(SRCDIR)/base
CXXFLAGS=-g $(HDRS)
CXX=g++
LDFLAGS=-g -s
AR=ar
ARFLAGS=rvs
LIBS=
#TARGET=dump extr treeify
TARGET=dump treeify

## make rules

all:		$(TARGET)

tools.o:	tools.C

dump:		dump.o tools.o
		$(CXX) dump.o tools.o -o dump
 
extr.o:		extr.C

extr:		extr.o tools.o
		$(CXX) extr.o tools.o -o extr
 
treeify.o:	treeify.C

treeify:	treeify.o tools.o
		$(CXX) treeify.o -o treeify
 
treeify.o:	treeify.C


.PHONY:		clean
clean:
		-rm -f  *.bak *.o *.ii core a.out $(TARGET)
