#!/usr/bin/env python
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
import sys
import argparse
from blisslib import SVG, Document, Address, makeDoc

#-----------------------------------------------------------------------------
class AddressList(Document):
    def __init__(self, path):
        super().__init__(path)
        self.nextX = 8.5
        self.nextY = 38

    def _updateAddress(self, address, row):
        address.data = row
        self._updateDetails(address)
        self._updateOccupancy(address)

    def _createAddress(self, row):
        xml = """
    <g
       transform="translate({1}, {2})"
       inkscape:label="{0[rapid]}">
      <use
         height="100%"
         width="100%"
         x="122.5"
         y="-4.1"
         transform="scale(1.4,1.4)"
         inkscape:label="symbolOccupancy"
         xlink:href="#question_mark_symbol" />
      <text
         style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:2.82222223px;font-family:Overpass;-inkscape-font-specification:'Overpass, Normal';font-variant-ligatures:normal;font-variant-caps:normal;font-variant-numeric:normal;font-feature-settings:normal;text-align:center;writing-mode:lr-tb;text-anchor:middle;stroke-width:0.26458332"
         x="171.54761"
         y="1.2784872"
         inkscape:label="textRAPID">{0[rapid]}</text>
      <text
         style="font-style:normal;font-variant:normal;font-weight:bold;font-stretch:normal;font-size:5.64444447px;font-family:Overpass;-inkscape-font-specification:'Overpass, Bold';font-variant-ligatures:normal;font-variant-caps:normal;font-variant-numeric:normal;font-feature-settings:normal;text-align:start;writing-mode:lr-tb;text-anchor:start"
         x="9.8367767"
         y="2.2662649"
         inkscape:label="textNumber">{0[number]}</text>
      <text
         style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:3.88055563px;line-height:1.25;font-family:'Liberation Serif';-inkscape-font-specification:'Liberation Serif, Normal';font-variant-ligatures:normal;font-variant-caps:normal;font-variant-numeric:normal;font-feature-settings:normal;text-align:start;letter-spacing:0px;word-spacing:0px;writing-mode:lr-tb;text-anchor:start;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.26458332"
         x="96.377472"
         y="1.2826384"
         inkscape:label="textPhone"
         xml:space="preserve"></text>
      <text
         style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:3.88055563px;line-height:1.25;font-family:'Liberation Serif';-inkscape-font-specification:'Liberation Serif, Normal';font-variant-ligatures:normal;font-variant-caps:normal;font-variant-numeric:normal;font-feature-settings:normal;text-align:start;letter-spacing:0px;word-spacing:0px;writing-mode:lr-tb;text-anchor:start;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.26458332"
         x="31.819035"
         y="1.6075971"
         inkscape:label="textNames"
         xml:space="preserve"></text>
    </g>
        """.format(row, self.nextX, self.nextY)
        element = SVG.Element.fromstring(xml)
        self.layer.append(element)
        self.nextY += 6.4
        address = Address(element, row)
        self._updateDetails(address)
        self._updateOccupancy(address)
        return address

    def _updateDetails(self, address):
        names = address.element.find("svg:text[@inkscape:label='textNames']")
        names = self._textOrTspan(names)
        names.text = address.names
        phone = address.element.find("svg:text[@inkscape:label='textPhone']")
        phone = self._textOrTspan(phone)
        phone.text = address.phone

#-----------------------------------------------------------------------------
def parseArgs(rawArgs):
    parser = argparse.ArgumentParser(description="Make an address list")
    parser.add_argument("--no-deletes", action='store_true',
                       help="leave stale addresses on the list")
    parser.add_argument("inpath", metavar="Addresses.csv")
    parser.add_argument("outpath", metavar="AddressList.svg",
                        nargs="?", default="list.svg")
    args = parser.parse_args(rawArgs)
    return args

#-----------------------------------------------------------------------------
def main(rawArgs=sys.argv[1:]):
    args = parseArgs(rawArgs)
    addrs = AddressList(args.outpath)
    makeDoc(args.inpath, addrs, clearStale=not args.no_deletes)

#-----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
