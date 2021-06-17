#!/usr/bin/env python
import sys
import argparse
from itertools import chain
from decimal import Decimal
from contextlib import AbstractContextManager
from pdfplumber import PDF
from csv import DictWriter

class CloserMixin(AbstractContextManager):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class AddressWriter(DictWriter, CloserMixin):
    fields = ['number',
              'address',
              'postcode',
              'title',
              'area',
              'assessment#',
              'valuation#',
              'zone',
              'service',
              'page#']

    def __init__(self, path):
        if path == "-":
            self.fileOut = sys.stdout
        else:
            self.fileOut = open(path, "w", newline='')
        super().__init__(self.fileOut, self.fields, extrasaction="ignore")

    def close(self):
        if self.fileOut is not sys.stdout:
            self.fileOut.close()


class AssessmentRecord:
    HeadingVLines = [  21,  115,    # Rates Assessment:
                      182,  280,    # Valuation Number:
                      404,  468,    # Rating Zone:
                      670,  733,    # Rating Class:
                      945, 1020,    # total land area:
                     1150]
    AddressVLines = [  24,    # Parcel no.
                       71,    # Address
                      241,    # postcode
                      292,    # parcel_title
                      560,    # area
                      634]

    def __init__(self, page, top, bottom):
        self.page   = page
        self.top    = top
        self.bottom = bottom
        self.info   = self._getHeader()

    def _getHeader(self):
        box = (self.HeadingVLines[0], self.top,
               self.HeadingVLines[-1], self.top + 12)
        header = self.page.crop(box)
        tblSettings = {'vertical_strategy': "explicit",
                       'explicit_vertical_lines': self.HeadingVLines,
                       'horizontal_strategy': "text"}
        row = header.extract_table(tblSettings)[0]
        info = {'page#':        self.page.page_number,
                'assessment#':  row[1],
                'valuation#':   row[3],
                'zone':         row[5],
                'service':      row[7]}
        return info

    def getAddressRows(self):
        box = (self.AddressVLines[0], self.top + 28,
               self.AddressVLines[-1], self.bottom)
        section = self.page.crop(box)
        tblSettings = {'vertical_strategy': "explicit",
                       'explicit_vertical_lines': self.AddressVLines,
                       'horizontal_strategy': "text"}
        tbl = section.extract_table(tblSettings)
        for row in tbl[1:]:
            addrParts = row[1].split(maxsplit=1)
            if len(addrParts) == 2 and addrParts[0][0].isdigit():
                number, address = addrParts
            else:
                number, address = "", row[1]

            info = {'parcel#':   row[0],
                    'number':    number,
                    'address':   address,
                    'postcode':  row[2],
                    'title':     row[3],
                    'area':      row[4]}
            info.update(self.info)
            yield info


class RatingInformation(CloserMixin):
    def __init__(self, path, postcode=None, pages=None):
        self.postcode = postcode
        self.pdf = PDF.open(path, pages=pages)

    def close(self):
        self.pdf.close()

    def getAddresses(self, postcode=None):
        for page in self.pdf.pages:
            for record in self._getAssessmentRecords(page):
                for row in record.getAddressRows():
                    if self.postcode in (None, row['postcode']):
                        yield row
            page.close()

    def _getAssessmentRecords(self, page):
        words = page.extract_words(extra_attrs=['size'])
        hLines = [word['top'] for word in words
                  if word['text'] == "Rates" and
                     word['size'] == Decimal("11.999")] + [810]
        top = hLines[0]
        for bottom in hLines[1:]:
            yield AssessmentRecord(page, top, bottom)
            top = bottom


def saveAddresses(pdfPath, csvPath, **kwargs):
    with RatingInformation(pdfPath, **kwargs) as prid, \
         AddressWriter(csvPath) as csv:
        csv.writeheader()
        csv.writerows(prid.getAddresses())

def parseArgs(rawArgs):
    def parsePageSpec(pgSpec):
        pages = []
        for arg in pgSpec.split(","):
            if "-" in arg:
                start, end = map(int, arg.split("-"))
                pages.extend(int(pg) for pg in range(start, end + 1))
            else:
                pages.append(int(arg))
        return pages

    parser = argparse.ArgumentParser(description=
        "Plumb the Public Rates Information Database")
    parser.add_argument("--pages", type=parsePageSpec)
    parser.add_argument("--postcode")
    parser.add_argument("inpath", metavar="PRIDFile.pdf")
    parser.add_argument("outpath", metavar="Outfile.csv",
                        nargs="?", default="-")
    args = parser.parse_args(rawArgs)
    return args


def main(rawArgs=sys.argv[1:]):
    args = parseArgs(rawArgs)
    saveAddresses(args.inpath,
                  args.outpath,
                  postcode=args.postcode,
                  pages=args.pages)


if __name__ == "__main__":
    main()
