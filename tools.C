#include "tools.H"
#include <cstdlib>
#include <cctype>
#include <iostream>
#include <iomanip>

using namespace std;

static const size_t rowLength = 0x10;

void dump(ostream& out, unsigned char* addr, size_t length)
{
    out << setfill('0') << hex;

    size_t i = 0;
    while (i < length)
    {
        out << setw(7) << (addr+i) << ":  "; 

        size_t j; 
        for (j = 0; j < min(rowLength, length-i); ++j)
        {
            out << setw(2) << static_cast<int>(addr[i+j]) << " "; 
        }
        while (j++ < rowLength)
        {
            out << "   "; 
        }
        out << "  "; 
        for (j = 0; j < min(rowLength, length-i); ++j)
        {
            if (isprint(addr[i+j]))
                out << addr[i+j]; 
            else
                out << "."; 
        }
        out << endl;
        i += rowLength;
    }
}

void dump(ostream& out, istream& in, size_t length)
{
    out << setfill('0') << hex;

    size_t i = 0;
    while (i < length && in)
    {
        char c;
        string str;
        out << setw(8) << i << ":  "; 

        size_t j; 
        for (j = 0; j < min(rowLength, length-i) && in.get(c); ++j)
        {
            if (isprint(c))
                str += c;
            else
                str += "."; 

            unsigned char x = static_cast<unsigned char>(c);
            out << setw(2) << static_cast<int>(x) << " "; 
        }
        while (j++ < rowLength)
        {
            out << "   "; 
        }
        out << "  " << str << endl;
        i += rowLength;
    }
}

