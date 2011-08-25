// extr
//
// simple tool to extract the readable portion of a binary file to the standard
// output stream
// i.e. my own version on strings

// $Id$
// Copyright 1998-2000, D J Moore

// $Log$


#include <iostream>
#include <fstream>
#include <string>
#include <cctype>


int main(int argc, char* argv[])
{
    if (argc != 2 && argc !=3)
    {
        cout << "usage: " << argv[0] << " dumpfile [threshhold]" << endl;
        exit(1);
    }

    int thresh = 10;

    if (argc == 3)
    {
        thresh = atoi(argv[2]);
    }

    string buffer;
    char c;
    bool inText = false;

    ifstream in(argv[1]);
    in.get(c);
    while (in)
    {
        if (inText)
        {
            if (isprint(c) || c == '\n' || c == '\r')
            {
                cout.put(c);
            }
            else
            {
                inText = false;
            }
        }
        else
        {
            if (isprint(c) || c == '\n' || c == '\r')
            {
                buffer += c;
                if (buffer.length() > thresh)
                {
                    cout << endl << endl << buffer;
                    buffer = "";
                    inText = true;
                }
            }
            else
            {
                buffer.erase();
            }
        }
    
        in.get(c);
    }
    
    return 0;
}

