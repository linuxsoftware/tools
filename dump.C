// dump
//
// simple tool to dump the contents of a file as hex to the standard
// output stream

// $Id$
// Copyright 1998-2000, D J Moore

// $Log$

#include "tools.H"
#include <fstream>
#include <iostream>
using namespace std;

int main(int argc, char* argv[])
{
    ifstream in(argv[1]);
    cout << "Dump of " << argv[1] << endl;
    dump(cout, in);
    return 0;
}
