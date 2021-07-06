#!/usr/bin/env python
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
import sys
import argparse
from blisslib import SVG, Document, Address, makeDoc

#-----------------------------------------------------------------------------
class Map(Document):
    def __init__(self, path, landscape=False):
        super().__init__(path, landscape)
        widthAttr = self.tree.getroot().get('width')
        self.pageWidth = int("".join(d for d in widthAttr if d.isdigit()))

    def _updateAddress(self, address, row):
        address.data = row
        self._updateDetails(address)
        self._updateOccupancy(address)

    def _createAddress(self, row):
        xml = """
    <g
       transform="translate({1}, {2})"
       inkscape:label="{0[rapid]}">
      <path
         d="M 1.07721,5.949556 9.1092,2.642264"
         style="fill:none;fill-opacity:0.9875;stroke:#000000;stroke-width:0.16500001;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1;marker-start:url(#DotL)"
         inkscape:connector-curvature="0"
         inkscape:label="line" />
      <rect
         height="17.424252"
         ry="1.1693041"
         style="opacity:1;fill:#ffffff;fill-opacity:1;stroke:#000000;stroke-width:0.126;stroke-miterlimit:4.0999999;stroke-dasharray:none;stroke-opacity:1"
         width="15.111476"
         x="9.0878916"
         y="-0.03125304"
         inkscape:label="box" />
      <use
         height="100%"
         width="100%"
         x="14.766641"
         y="11.158503"
         inkscape:label="symbolOccupancy"
         xlink:href="#question_mark_symbol" />
      <text
         style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:1.05833328px;font-family:Overpass;-inkscape-font-specification:'Overpass, Normal';font-variant-ligatures:normal;font-variant-caps:normal;font-variant-numeric:normal;font-feature-settings:normal;text-align:center;writing-mode:lr-tb;text-anchor:middle;stroke-width:0.26458332"
         x="16.529512"
         y="1.397404"
         inkscape:label="textRAPID">{0[rapid]}</text>
      <text
         style="font-style:normal;font-variant:normal;font-weight:bold;font-stretch:normal;font-size:4.23333311px;font-family:Overpass;-inkscape-font-specification:'Overpass, Bold';font-variant-ligatures:normal;font-variant-caps:normal;font-variant-numeric:normal;font-feature-settings:normal;text-align:start;writing-mode:lr-tb;text-anchor:start"
         x="10.53698"
         y="5"
         inkscape:label="textNumber">{0[number]}</text>
      <text
         style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:1.76388889px;line-height:1.25;font-family:'Liberation Serif';-inkscape-font-specification:'Liberation Serif, Normal';font-variant-ligatures:normal;font-variant-caps:normal;font-variant-numeric:normal;font-feature-settings:normal;text-align:start;letter-spacing:0px;word-spacing:0px;writing-mode:lr-tb;text-anchor:start;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.26458332"
         x="9.6093454"
         y="7.5"
         inkscape:label="textDetails"
         xml:space="preserve"></text>
    </g>
        """.format(row, self.nextX, self.nextY)
        element = SVG.Element.fromstring(xml)
        self.layer.append(element)
        self.nextX += 25

        if self.nextX > self.pageWidth - 25:
            self.nextX = 5
            self.nextY += 20
        address = Address(element, row)
        self._updateDetails(address)
        self._updateOccupancy(address)
        return address

    def _updateDetails(self, address):
        text = address.element.find("svg:text[@inkscape:label='textDetails']")
        textContent = " ".join(txt.strip() for txt in text.itertext())
        dtlContent  = " ".join(dtl for dtl in address.details if dtl)
        if textContent == dtlContent:
            return         # don't update if the content has not changed
        attribs = {'x': text.get('x'),
                   'y': text.get('y'),
                   'sodipodi:role': "line"}
        text[:] = []       # clear old tspans
        y = float(attribs['y'])
        for dtl in address.details:
            tspan = SVG.SubElement(text, "svg:tspan", attribs)
            tspan.text = dtl
            y += 1.76389
            attribs['y'] = str(y)

#-----------------------------------------------------------------------------
def parseArgs(rawArgs):
    parser = argparse.ArgumentParser(description= "Make a map")
    parser.add_argument("--landscape", action='store_true',
                       help="default to landscape pages")
    parser.add_argument("--no-deletes", action='store_true',
                       help="leave stale addresses on the map")
    parser.add_argument("inpath", metavar="Addresses.csv")
    parser.add_argument("outpath", metavar="Map.svg",
                        nargs="?", default="map.svg")
    args = parser.parse_args(rawArgs)
    return args

#-----------------------------------------------------------------------------
def main(rawArgs=sys.argv[1:]):
    args = parseArgs(rawArgs)
    map = Map(args.outpath, args.landscape)
    makeDoc(args.inpath, map, clearStale=not args.no_deletes)

#-----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
