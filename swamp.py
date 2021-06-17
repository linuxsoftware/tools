#!/usr/bin/python
import sys
import re
import os
import os.path

class SourceFile:
    IgnoreWords = set(["getLogger", "getName", "setName",
                       "setDaemon", "isDaemon", "addHandler",
                       "basicConfig", "addFilter", "setLevel", "removeFilter",
                       "fileConfig", "getLoggerClass", "getLevelName",
                       "makeLogRecord", "setLoggerClass", "isEnabledFor",
                       "getEffectiveLevel", "findCaller", "makeRecord",
                       "cPickle", "cStringIO", "setUp", "tearDown"

                      ])

    def __init__(self, path):
        self.code      = ""
        self.newCode  = ""
        self.modified = False
        self.path      = path

    varRe = re.compile(r"(?<!['\"])\b[a-z_][a-z0-9_]*[A-Z]\w*")
    upperRe = re.compile(r'([A-Z])')

    def process(self):
        self.code = file(self.path, "rt").read()

        self.newCode = self.varRe.sub(self._processVar, self.code)

        if self.modified:
            print(self.path)
            try:
                os.remove(self.path+".bak")
            except:
                pass
            os.rename(self.path, self.path+".bak")
            file(self.path, "wt").write(self.newCode)

    def _processVar(self, match):
        def _processHump(match):
            return "_" + match.group(0).lower()
        word = match.group(0)
        word = word.replace("ID", "Id")
        if word.startswith("assert"):
            return word
        if word[0] == "'":
            return word
        if word in self.IgnoreWords:
            return word
        self.modified = True
        return self.upperRe.sub(_processHump, word)


class SourceTree:
    IgnoreDirs = ["migrations", "buildScripts", "productBuild", "static"]

    def __init__(self, recurse):
        self.recurse  = recurse
        self.srcFiles = []

    def search(self, path):
        if not os.path.isdir(path):
            dirEntries = [os.path.basename(path),]
            path = os.path.dirname(path)
        else:
            dirEntries = os.listdir(path)
        for entry in dirEntries:
            newpath = os.path.join(path, entry)
            if os.path.isfile(newpath):
                extn = os.path.splitext(entry)[1].lower()
                if extn in (".py", ".proto"):
                     self.srcFiles.append(newpath)
            elif self.recurse and os.path.isdir(newpath):
                if entry not in self.IgnoreDirs:
                    newpath = os.path.join(path, entry)
                    self.search(newpath)

    def process(self):
        for entry in self.srcFiles:
            srcFile = SourceFile(entry)
            srcFile.process()

    def revert(self, path):
        for entry in os.listdir(path):
            newpath = os.path.join(path, entry)
            if os.path.isfile(newpath):
                path2 = os.path.splitext(newpath)
                if path2[1] == ".bak":
                    try:
                        os.remove(path2[0])
                    except:
                        pass
                    os.rename(newpath, path2[0])
                    sys.stdout.write(".")
                    sys.stdout.flush()

            elif self.recurse and os.path.isdir(newpath):
                if entry not in self.IgnoreDirs:
                    newpath = os.path.join(path, entry)
                    self.revert(newpath)


if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1 and args[1] in ("--help", "-h", "-?"):
        print("This script will convert all the camelCase variables in Python")
        print("source files to snake_case print")
        print("swamp.py [flags] [source-dir]")
        print("flags: --no-recurse")
        print("         --revert")
        print("         --help")
        print("note:  the default source-dir is .")
        sys.exit(0)

    recurse = True
    if "--no-recurse" in args:
        recurse = False
        args.remove("--no-recurse")

    revert  = False
    if "--revert" in args:
        revert = True
        args.remove("--revert")

    sourcePath = "."
    if len(args) > 1:
        sourcePath = args[1]

    tree = SourceTree(recurse)
    if revert:
        tree.revert(sourcePath)
        print("")
        sys.exit(0)

    tree.search(sourcePath)
    tree.process()


