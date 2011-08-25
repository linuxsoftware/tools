#ifndef tools_H__
#define tools_H__

#include <iosfwd>
#include <memory>
#include <climits>

void dump(std::ostream& out, unsigned char* addr, size_t length);
void dump(std::ostream& out, std::istream& in, size_t length=UINT_MAX);

#endif
