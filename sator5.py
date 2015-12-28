#!/usr/bin/python
import sys

class SquareBuilder:
    def __init__(self, filename):
        self.allowOuterPalindromes = False
        self.matchingWords = []
        self.palindromes = []
        with open(filename) as dictIn:
            self._readMatchingWords(dictIn)

    def _readMatchingWords(self, dictIn):
        words = set(word.rstrip('\n').lower()
                    for word in dictIn if len(word) == 6)
        for word1 in words:
            word2 = word1[::-1]
            if word2 in words:
                if self.allowOuterPalindromes or word1 != word2:
                    self.matchingWords.append(word1)
                if word1 == word2:
                    self.palindromes.append(word1)

    def __iter__(self):
        return self._buildSquares()

    def _buildSquares(self):
        for word0 in self.matchingWords:
            for word1 in self.matchingWords:
                if self._matchOuterWords(word0, word1):
                    for word2 in self.palindromes:
                        if self._matchInnerWord(word0, word1, word2):
                            yield [word0,
                                   word1,
                                   word2,
                                   word1[::-1],
                                   word0[::-1]]

    def _matchOuterWords(self, word0, word1):
        return ((word1[0] == word0[1] and word1[-1] == word0[-2]) or
                (word1[-1] == word0[1] and word1[0] == word0[-2]))

    def _matchInnerWord(self, word0, word1, word2):
        return (word2[0] == word0[2] and word2[1] == word1[2])

def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "/usr/share/dict/words"
    for i, square in enumerate(SquareBuilder(filename)):
        print(i)
        for line in square:
            print(line)
        print("")

if __name__ == "__main__":
    main()





