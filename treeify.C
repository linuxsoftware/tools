// treeify
//
// simple tool to read directory paths from the standard input
// (eg. streamed from find) and output them in a tree format to the
// standard output stream

// $Id$
// Copyright 1998-2000, D J Moore

// $Log$


#include <iostream>
#include <set>
#include <string>
#include <algorithm>

using namespace std;


class Node;
typedef bool (*Compare)(const Node* lhs, const Node* rhs);

class Node
{
public:
   Node(const string& name = "");
   ~Node();
   const string& name()  const;
   void          add(const string& str);
   void          print(const string& connect = "");

private:
   typedef set<Node*, Compare>   Nodes;
   typedef Nodes::const_iterator CNodeIter;

   string            m_name;
   Nodes             m_nodes;
   static const char c_separator = '/';
};

bool compare(const Node* lhs, const Node* rhs)
{
   return lhs->name() < rhs->name();
}

Node::Node(const string& name) :
   m_name(name),
   m_nodes(&compare)
{
}

Node::~Node()
{
   for (CNodeIter iter = m_nodes.begin(); iter != m_nodes.end(); ++iter) {
      delete *iter;
   }
}

const string& Node::name()  const
{
   return m_name;
}

void Node::add(const string& str)
{
   string::size_type pos = str.find(c_separator);
   string name = str.substr(0, pos);
   Node target(name);
   CNodeIter iter = m_nodes.find(&target);

   if (iter == m_nodes.end()) {
      iter = m_nodes.insert(new Node(name)).first;
   }

   if (pos != string::npos) {
      Node* pNode = *iter;
      pNode->add(str.substr(pos + 1));
   }
}

void Node::print(const string& connect)
{
   for (CNodeIter iter = m_nodes.begin(); iter != m_nodes.end(); ++iter) {
      Node* pNode    = *iter;
      CNodeIter next = iter;
      ++next;

      if (next != m_nodes.end()) {
         cout << connect << "+---" << pNode->name() << endl;
         pNode->print(connect + "|   ");
      } else {
         cout << connect << "\\---" << pNode->name() << endl;
         pNode->print(connect + "    ");
      }
   }
}

int main(int argc, char* argv[])
{
   string str;
   Node root;

   getline(cin, str);
   while(cin) {
      root.add(str);
      getline(cin, str);
   }

   root.print();
    
   return 0;
}

