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

dump:		dump.o
		$(CXX) dump.o -L$(LIBDIR) -lBase -o dump
 
#extr.o:		extr.C
#
#extr:		extr.o
#		$(CXX) extr.o -L$(LIBDIR) -lBase -o extr
 
treeify.o:	treeify.C

treeify:	treeify.o
		$(CXX) treeify.o -o treeify
 
treeify.o:	treeify.C


.PHONY:		clean
clean:
		-rm -f  *.bak *.o *.ii core a.out $(TARGET)
