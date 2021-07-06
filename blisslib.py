#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
import sys
import os
import datetime as dt
from itertools import chain
from csv import DictReader
from pathlib import Path
import xml.etree.ElementTree as ET


#-----------------------------------------------------------------------------
class SVG:
    NS = {"cc":       "http://creativecommons.org/ns#",
          "svg":      "http://www.w3.org/2000/svg",
          "":         "http://www.w3.org/2000/svg",
          "xlink":    "http://www.w3.org/1999/xlink",
          "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
          "inkscape": "http://www.inkscape.org/namespaces/inkscape"}
    for prefix, uri in NS.items():
        ET.register_namespace(prefix, uri)

    def _expand(tag):
        if tag[0] != '{' and ':' in tag:
            prefix, tag = tag.split(":", 1)
            tag = "{%s}%s" % (SVG.NS[prefix], tag)
        return tag

    def _getParser():
        builder = ET.TreeBuilder(element_factory=SVG.Element)
        parser = ET.XMLParser(target=builder)
        return parser

    class Element(ET.Element):
        @classmethod
        def fromstring(cls, text):
            nsXml = "\n".join('xmlns:{}="{}"'.format(prefix,uri) if prefix
                              else 'xmlns="{}"'.format(uri)
                              for prefix, uri in SVG.NS.items())
            docXml = "<svg {}>{}</svg>".format(nsXml, text)
            root = ET.XML(docXml, parser=SVG._getParser())
            return root[0]

        def find(self, path, ns=None):
            if ns is None:
                ns = SVG.NS
            return super().find(path, ns)

        def findall(self, path, ns=None):
            if ns is None:
                ns = SVG.NS
            return super().findall(path, ns)

        def get(self, key, default=None):
            return super().get(SVG._expand(key), default)

        def set(self, key, value):
            return super().set(SVG._expand(key), value)

    def SubElement(parent, tag, attrib={}, **extra):
        tag = SVG._expand(tag)
        attrib = {SVG._expand(k): v for k,v in attrib.items()}
        return ET.SubElement(parent, tag, attrib, **extra)

    class Tree(ET.ElementTree):
        @classmethod
        def fromfile(cls, source):
            tree = cls()
            tree.parse(source, parser=SVG._getParser())
            return tree

        @classmethod
        def fromstring(cls, text):
            root = ET.XML(text, parser=SVG._getParser())
            return cls(root)


#-----------------------------------------------------------------------------
class Address:
    def __init__(self, element, data=None):
        self.element = element
        self.data    = data

    def __prop(item):
        def get(obj):
            if obj.data is not None:
                return obj.data.get(item)
        return property(get)
    names       = __prop('names')
    phone       = __prop('phone')
    number      = __prop('number')
    address     = __prop('address')
    rapid       = __prop('rapid')
    occupancy   = __prop('occupancy')

    @property
    def details(self):
        if self.data is None:
            return ""
        return [dtl.strip() for dtl in chain(self.names.split(","), "\n",
                                             self.phone.split(","))]

#-----------------------------------------------------------------------------
class Document:
    def __init__(self, path, landscape=False):
        self.path = Path(path)
        self.addresses = {}
        self.nextX = self.nextY = 5
        if self.path.is_file():
            self.load()
        else:
            self.new(landscape)
        self._updateDate()

    def load(self):
        self.tree = SVG.Tree.fromfile(self.path)
        self.layer = self._getAddressLayer()
        self.addresses.clear()
        self.nextX = self.nextY = 5
        for group in self.layer.findall("svg:g"):
            label = group.get("inkscape:label")
            rapid = group.find("svg:text[@inkscape:label='textRAPID']")
            rapid = self._textOrTspan(rapid)
            if rapid is None or rapid.text.strip() == "":
                print("Group {} has no RAPID text, skipping.".format(label))
                continue
            if rapid.text in self.addresses:
                raise ValueError("Duplicated RAPID {}".format(rapid.text))
            self.addresses[rapid.text.strip()] = Address(group)

    def new(self, landscape):
        self.addresses.clear()
        self.nextX = self.nextY = 5
        self.tree = SVG.Tree.fromstring(self._createBlankDocXml(landscape))
        self.layer = self._getAddressLayer()

    def save(self, backup=True):
        if backup and self.path.exists():
            stem = self.path.stem
            backupPath = self.path.with_name("{}.bak".format(stem))
            uniq = 1
            while backupPath.exists():
                backupPath = self.path.with_name("{}-{}.bak".format(stem, uniq))
                uniq += 1
            os.rename(self.path, backupPath)
        with self.path.open("w") as fileOut:
            self.write(fileOut)

    def write(self, fileOut):
        fileOut.write('<?xml version="1.0" encoding="utf-8" ?>\n')
        self.tree.write(fileOut, encoding='unicode')
        fileOut.write('\n')

    def addAddress(self, row):
        rapid = row['rapid']
        address = self.addresses.get(rapid)
        if address:
            self._updateAddress(address, row)
        else:
            self.addresses[rapid] = self._createAddress(row)

    def _updateAddress(self, address, row):
        raise NotImplementedError()

    def _createAddress(self, row):
        raise NotImplementedError()

    def _updateDetails(self, address):
        raise NotImplementedError()

    def _updateOccupancy(self, address):
        symbols = {"unknown":       "question_mark_symbol",
                   "Vacant":        "empty_square_symbol",
                   "Permanent":     "house_symbol",
                   "Occasional":    "bach_symbol",
                   "Holidays":      "bach_in_sun_symbol",
                   "Accommodation": "bedroom_symbol",
                   "Business":      "warehouse_symbol"}
        occupancySymbol = symbols.get(address.occupancy,
                                      symbols['unknown'])
        use = address.element.find("svg:use[@inkscape:label='symbolOccupancy']")
        use.set('xlink:href', "#"+occupancySymbol)

    def clearStaleAddresses(self):
        freshAddresses = {}
        for rapid, address in self.addresses.items():
            if address.data is None:
                self.layer.remove(address.element)
            else:
                freshAddresses[rapid] = address
        self.addresses = freshAddresses

    def _getAddressLayer(self):
        layer = self.tree.find("svg:g"
                               "[@inkscape:groupmode='layer']"
                               "[@inkscape:label='Addresses']")
        if layer is None:
            raise RuntimeError("No Addresses layer in map")
        return layer

    def _updateDate(self):
        layer = self.tree.find("svg:g"
                               "[@inkscape:groupmode='layer']"
                               "[@inkscape:label='Base']")
        text = layer.find(".//svg:text"
                          "[@inkscape:label='textLastUpdated']")
        if text:
            element = self._textOrTspan(text)
            today = dt.date.today()
            element.text = "Last updated: {:%e %B %Y}".format(today)

    def _textOrTspan(self, text):
        if text:
            tspan = text.find("svg:tspan")
            if tspan is not None:
                text = tspan
        return text

    def _createBlankDocXml(self, landscape=False):
        if landscape:
            width  = 297
            height = 210
        else:
            width  = 210
            height = 297
        xml = """
<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:xlink="http://www.w3.org/1999/xlink"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   height="{2}mm"
   version="1.1"
   viewBox="0 0 {1} {2}"
   width="{1}mm"
   sodipodi:docname="{0}"
   inkscape:version="0.92.4 (unknown)">
  <defs>
    <marker
       id="DotL"
       orient="auto"
       refX="0.0"
       refY="0.0"
       style="overflow:visible"
       inkscape:isstock="true"
       inkscape:stockid="DotL">
      <path
         d="M -2.5,-1.0 C -2.5,1.7600000 -4.7400000,4.0 -7.5,4.0 C -10.260000,4.0 -12.5,1.7600000 -12.5,-1.0 C -12.5,-3.7600000 -10.260000,-6.0 -7.5,-6.0 C -4.7400000,-6.0 -2.5,-3.7600000 -2.5,-1.0 z "
         style="fill-rule:evenodd;stroke:#000000;stroke-width:1pt;stroke-opacity:1;fill:#ffffff;fill-opacity:0.9875"
         transform="scale(0.8) translate(7.4, 1)" />
    </marker>
    <symbol
       transform="translate(-4.202449,-6.2768615)"
       id="question_mark_symbol">
      <path
         inkscape:connector-curvature="0"
         style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:7.05555534px;font-family:'Liberation Sans';-inkscape-font-specification:'Liberation Sans, Normal';font-variant-ligatures:normal;font-variant-caps:normal;font-variant-numeric:normal;font-feature-settings:normal;text-align:start;writing-mode:lr-tb;text-anchor:start;stroke-width:0.07000434"
         d="m 11.819613,10.386397 q 0,0.06836 -0.02005,0.122143 -0.02005,0.05378 -0.05743,0.09935 -0.03737,0.04558 -0.122143,0.107559 l -0.07292,0.05378 q -0.06563,0.0474 -0.09753,0.100267 -0.0319,0.05196 -0.03281,0.113939 h -0.159515 q 0.0018,-0.06289 0.01914,-0.110293 0.01823,-0.0474 0.04649,-0.08386 0.02826,-0.03646 0.06381,-0.06472 0.03555,-0.02917 0.07201,-0.05469 0.03646,-0.02644 0.0711,-0.05196 0.03555,-0.02643 0.06289,-0.05834 0.02735,-0.0319 0.04375,-0.07201 0.01732,-0.04011 0.01732,-0.09389 0,-0.103912 -0.0711,-0.164073 -0.07019,-0.06016 -0.197799,-0.06016 -0.127612,0 -0.202356,0.06381 -0.07474,0.0638 -0.08751,0.17501 l -0.167719,-0.01094 q 0.0237,-0.180479 0.142196,-0.2771 0.118497,-0.09662 0.313561,-0.09662 0.203268,0 0.319942,0.09662 0.116674,0.09571 0.116674,0.266162 z m -0.569696,0.940683 v -0.183214 h 0.177745 v 0.183214 z" />
      <path
         inkscape:connector-curvature="0"
         d="M 10.606631,9.8632595 H 12.1121 v 1.6844015 h -1.505469 z"
         style="opacity:1;fill:none;fill-opacity:0.9875;stroke:#000000;stroke-width:0.06614583;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" />
    </symbol>
    <symbol
       transform="translate(-3.0743276,-7.6979758)"
       id="empty_square_symbol">
      <path
         style="opacity:1;fill:none;fill-opacity:0.9875;stroke:#000000;stroke-width:0.06614583;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1"
         d="m 9.4630872,11.252076 h 1.5375958 v 1.750108 H 9.4630872 Z"
         inkscape:connector-curvature="0" />
    </symbol>
    <symbol
       id="house_symbol">
      <g
         transform="matrix(0.13576643,0,0,0.13576643,5.5080736,2.4768084)">
        <path
           d="m 2.7112039,20.619155 c 0,0.146244 0.1183392,0.264583 0.2645834,0.264583 H 20.836713 c 0.146244,0 0.264583,-0.118339 0.264583,-0.264583 v -1.151351 c 0,-0.146244 -0.118339,-0.264584 -0.264583,-0.264584 H 19.458761 V 8.9170267 h 1.003814 c 0.112397,0 0.212649,-0.071055 0.249597,-0.1769917 0.03721,-0.1061951 0.0034,-0.2242757 -0.08449,-0.2942974 L 13.791923,2.9866394 c -0.09664,-0.076998 -0.233578,-0.076998 -0.330212,0 L 8.561283,6.9003378 3.8408509,8.3669312 C 3.7302633,8.4012961 3.6548158,8.5036155 3.6548158,8.6196289 v 1.3280842 c 0,0.083974 0.040049,0.1632979 0.1077455,0.2131649 0.045992,0.03385 0.1010274,0.05142 0.1568378,0.05142 0.026355,0 0.05271,-0.0039 0.078548,-0.01188 l 0.1289328,-0.04007 V 19.20322 H 2.9757873 c -0.1462442,0 -0.2645834,0.11834 -0.2645834,0.264584 z M 13.626817,3.5318258 19.707324,8.3878603 h -8.172886 v -0.528973 l 0.219367,-0.068148 C 11.864392,7.7563742 11.93984,7.6540548 11.93984,7.5380413 V 6.2099571 c 0,-0.083974 -0.04005,-0.1632977 -0.107746,-0.2131653 -0.0677,-0.049868 -0.15477,-0.064337 -0.235386,-0.039532 l -1.6477674,0.511935 z m 5.302777,5.3852009 V 19.20322 H 11.534438 V 8.9170267 Z M 4.1839825,8.814449 8.7039424,7.4100936 c 0.027744,-0.00362 0.053727,-0.012113 0.079662,-0.024757 L 11.410673,6.5691073 V 7.3432202 L 4.1839822,9.5885611 V 8.8144482 Z m 4.836914,4.928898 H 6.5158816 c -0.1462442,0 -0.2645834,0.118339 -0.2645834,0.264583 v 5.19529 H 4.6560467 V 9.9959499 L 11.005272,8.0232991 V 19.203221 H 9.2854799 V 14.00793 c 0,-0.146244 -0.1183392,-0.264583 -0.2645834,-0.264583 z M 8.7563132,14.272514 V 19.20322 H 6.7804649 V 14.272514 Z M 3.2403706,19.732387 H 20.572129 v 0.622185 H 3.2403706 Z"
           style="stroke-width:0.26458332"
           inkscape:connector-curvature="0" />
        <path
           d="m 12.915232,16.003674 h 3.80907 c 0.146244,0 0.264584,-0.118339 0.264584,-0.264583 v -3.80907 c 0,-0.146244 -0.11834,-0.264583 -0.264584,-0.264583 h -3.80907 c -0.146244,0 -0.264583,0.118339 -0.264583,0.264583 v 3.80907 c 0,0.146244 0.118339,0.264583 0.264583,0.264583 z m 2.169119,-3.809069 h 1.375368 v 1.375368 h -1.375368 z m 0,1.904534 h 1.375368 v 1.375369 h -1.375368 z m -1.904535,-1.904534 h 1.375368 v 1.375368 h -1.375368 z m 0,1.904534 h 1.375368 v 1.375369 h -1.375368 z"
           style="stroke-width:0.26458332"
           inkscape:connector-curvature="0" />
        <path
           d="m 9.2854799,11.415841 c 0,-0.146245 -0.1183392,-0.264584 -0.2645834,-0.264584 H 6.5158816 c -0.1462442,0 -0.2645834,0.118339 -0.2645834,0.264584 v 1.100191 c 0,0.146244 0.1183392,0.264583 0.2645834,0.264583 h 2.5050149 c 0.1462442,0 0.2645834,-0.118339 0.2645834,-0.264583 z M 8.7563132,12.251449 H 6.7804649 v -0.571025 h 1.9758483 z"
           style="stroke-width:0.26458332"
           inkscape:connector-curvature="0" />
      </g>
    </symbol>
    <symbol
       transform="translate(-3.380754,-0.01208557)"
       id="bach_symbol">
      <g transform="matrix(0.12726325,0,0,0.12726325,9.0036372,2.8840763)">
        <path
           style="stroke-width:0.26458332"
           d="M 22.069712,18.600027 H 21.53189 v -0.884442 c 0,-0.146115 -0.118468,-0.264583 -0.264584,-0.264583 H 19.548032 V 6.8480316 l 0.465733,-0.076481 c 0.127899,-0.021058 0.221692,-0.1315164 0.221692,-0.2610951 V 4.947889 c 0,-0.077644 -0.03411,-0.151412 -0.09328,-0.2016672 -0.0593,-0.050385 -0.136942,-0.072089 -0.214198,-0.059428 L 3.7987346,7.3352112 c -0.1278991,0.021058 -0.221692,0.1315165 -0.221692,0.2610951 v 1.5626953 c 0,0.077644 0.034106,0.1514121 0.093276,0.2016673 0.048188,0.040954 0.1090372,0.062916 0.1713074,0.062916 0.014211,0 0.028551,-0.00116 0.042891,-0.00349 l 0.2498556,-0.041034 c -0.034268,0.5627402 -0.028341,1.6977641 -0.016021,4.0180521 0.00909,1.710167 0.025371,3.414633 0.031765,4.053887 H 2.5451935 c -0.1461151,0 -0.2645833,0.118468 -0.2645833,0.264583 v 0.884442 H 1.7427877 c -0.1461151,0 -0.2645834,0.118468 -0.2645834,0.264583 0,0.146116 0.1184683,0.264584 0.2645834,0.264584 H 22.069712 c 0.146115,0 0.264584,-0.118468 0.264584,-0.264584 0,-0.146115 -0.118469,-0.264583 -0.264584,-0.264583 z M 4.1062092,8.8473928 V 7.8209696 L 19.706291,5.2594981 V 6.285792 Z M 16.660223,11.436899 h -5.363884 c -0.146115,0 -0.264583,0.118468 -0.264583,0.264583 v 5.74952 H 4.6792848 C 4.6483759,14.452574 4.621698,10.214234 4.6595347,9.2928276 L 19.018865,6.9349289 V 17.451002 h -2.094058 v -5.74952 c 0,-0.146115 -0.118468,-0.264583 -0.264584,-0.264583 z m -0.264583,0.529166 v 5.484937 h -4.834718 v -5.484937 z m 4.607083,6.633962 H 2.8097768 v -0.619858 h 1.6076539 0.00284 16.5824503 z"
           inkscape:connector-curvature="0" />
        <path
           style="stroke-width:0.26458332"
           d="M 9.4866301,11.658591 H 5.6198119 c -0.1461151,0 -0.2645833,0.118468 -0.2645833,0.264583 v 3.866818 c 0,0.146115 0.1184682,0.264584 0.2645833,0.264584 h 3.8668182 c 0.1461151,0 0.2645834,-0.118469 0.2645834,-0.264584 v -3.866818 c 0,-0.146115 -0.118468,-0.264583 -0.2645834,-0.264583 z m -2.198057,3.866818 H 5.8843952 v -1.404307 h 1.4041779 z m 0,-1.933474 H 5.8843952 v -1.404178 h 1.4041779 z m 1.9334737,1.933474 h -1.404307 v -1.404307 h 1.404307 z m 0,-1.933474 h -1.404307 v -1.404178 h 1.404307 z"
           inkscape:connector-curvature="0" />
      </g>
    </symbol>
    <symbol
       transform="translate(-7.5459149,-0.04585104)"
       id="bach_in_sun_symbol">
      <g transform="matrix(0.12864874,0,0,0.12864874,13.216743,2.4214872)">
        <path
           style="stroke-width:0.18010968"
           d="M 7.7980916,4.9180456 V 3.3272235 c 0,-0.099465 -0.080557,-0.1801095 -0.1801096,-0.1801095 -0.099553,0 -0.1801098,0.080645 -0.1801098,0.1801095 v 1.5908221 c 0,0.099465 0.080557,0.1801098 0.1801098,0.1801098 0.099553,0 0.1801096,-0.080645 0.1801096,-0.1801098 z"
           inkscape:connector-curvature="0" />
        <path
           style="stroke-width:0.18010968"
           d="m 4.8222366,5.9680113 c 0.035178,0.035178 0.08126,0.052767 0.1273431,0.052767 0.046083,0 0.092166,-0.017589 0.1273432,-0.052767 0.070355,-0.070355 0.070355,-0.1844189 0,-0.2546864 L 3.951941,4.588519 c -0.070355,-0.070355 -0.184331,-0.070355 -0.2546863,0 -0.070355,0.070355 -0.070355,0.1844188 0,0.2546863 z"
           inkscape:connector-curvature="0" />
        <path
           style="stroke-width:0.18010968"
           d="m 11.284023,4.588519 -1.124982,1.1248059 c -0.07036,0.070267 -0.07036,0.184331 0,0.2546864 0.03518,0.035178 0.08126,0.052767 0.127343,0.052767 0.04608,0 0.09217,-0.017589 0.127343,-0.052767 l 1.124982,-1.124806 c 0.07036,-0.070267 0.07036,-0.184331 0,-0.2546863 -0.07036,-0.070355 -0.184331,-0.070355 -0.254686,0 z"
           inkscape:connector-curvature="0" />
        <path
           style="stroke-width:0.18010968"
           d="m 11.763319,7.7524867 h 1.590734 c 0.09955,0 0.18011,-0.080645 0.18011,-0.1801098 0,-0.099465 -0.08056,-0.1801096 -0.18011,-0.1801096 h -1.590734 c -0.09955,0 -0.18011,0.080645 -0.18011,0.1801096 0,0.099465 0.08056,0.1801098 0.18011,0.1801098 z"
           inkscape:connector-curvature="0" />
        <path
           style="stroke-width:0.18010968"
           d="M 3.4726451,7.3922673 H 1.881911 c -0.099553,0 -0.1801097,0.080645 -0.1801097,0.1801096 0,0.099465 0.080557,0.1801098 0.1801097,0.1801098 h 1.5907341 c 0.099553,0 0.1801098,-0.080645 0.1801098,-0.1801098 0,-0.099465 -0.080557,-0.1801096 -0.1801098,-0.1801096 z"
           inkscape:connector-curvature="0" />
        <path
           sodipodi:open="true"
           d="M 4.8308135,10.281843 A 3.2034383,3.0102589 0 0 1 5.3292433,6.7719346 3.2034383,3.0102589 0 0 1 9.0362335,6.1359793 3.2034383,3.0102589 0 0 1 10.822336,9.2539627"
           sodipodi:end="0.13496829"
           sodipodi:start="2.6454716"
           sodipodi:ry="3.0102589"
           sodipodi:rx="3.2034383"
           sodipodi:cy="8.8489056"
           sodipodi:cx="7.6480312"
           sodipodi:type="arc"
           style="opacity:1;fill:none;fill-opacity:0.9875;stroke:#000000;stroke-width:0.40807244;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" />
        <path
           style="stroke-width:0.26458332"
           d="m 21.51476,22.270304 h -0.537823 v -0.884442 c 0,-0.146116 -0.118468,-0.264584 -0.264583,-0.264584 h -1.719275 v -10.60297 l 0.465734,-0.07648 c 0.127899,-0.02106 0.221692,-0.131516 0.221692,-0.261095 V 8.6181652 c 0,-0.077644 -0.03411,-0.151412 -0.09328,-0.2016672 C 19.527925,8.366113 19.450283,8.344409 19.373026,8.35707 L 3.2437821,11.005487 c -0.127899,0.02106 -0.221692,0.131517 -0.221692,0.261095 v 1.562696 c 0,0.07764 0.034106,0.151412 0.093276,0.201667 0.048188,0.04095 0.1090372,0.06292 0.1713074,0.06292 0.014211,0 0.028551,-0.0012 0.042891,-0.0035 l 0.2498556,-0.04103 c -0.034268,0.56274 -0.028341,1.697764 -0.016021,4.018052 0.00909,1.710167 0.025371,3.414634 0.031765,4.053887 h -1.604923 c -0.1461151,0 -0.2645834,0.118468 -0.2645834,0.264583 v 0.884442 H 1.1878352 c -0.1461151,0 -0.26458333,0.118469 -0.26458333,0.264584 0,0.146115 0.11846823,0.264583 0.26458333,0.264583 H 21.51476 c 0.146115,0 0.264583,-0.118468 0.264583,-0.264583 0,-0.146115 -0.118468,-0.264583 -0.264583,-0.264583 z M 3.5512568,12.517669 V 11.491246 L 19.151338,8.9297743 v 1.0262939 z m 12.5540142,2.589506 h -5.363885 c -0.146115,0 -0.264583,0.118468 -0.264583,0.264583 v 5.74952 H 4.1243324 C 4.0934235,18.12285 4.0667456,13.88451 4.1045823,12.963104 L 18.463912,10.605205 v 10.516073 h -2.094058 v -5.74952 c 0,-0.146115 -0.118468,-0.264583 -0.264583,-0.264583 z m -0.264583,0.529167 v 5.484936 H 11.00597 v -5.484936 z m 4.607083,6.633962 H 2.2548244 v -0.619859 h 1.6076539 0.00284 16.5824497 z"
           inkscape:connector-curvature="0" />
        <path
           style="stroke-width:0.26458332"
           d="M 8.9316777,15.328867 H 5.0648595 c -0.1461151,0 -0.2645834,0.118468 -0.2645834,0.264583 v 3.866818 c 0,0.146116 0.1184683,0.264584 0.2645834,0.264584 h 3.8668182 c 0.1461151,0 0.2645833,-0.118468 0.2645833,-0.264584 V 15.59345 c 0,-0.146115 -0.118468,-0.264583 -0.2645833,-0.264583 z m -2.198057,3.866818 H 5.3294428 v -1.404307 h 1.4041779 z m 0,-1.933474 H 5.3294428 v -1.404177 h 1.4041779 z m 1.9334737,1.933474 h -1.404307 v -1.404307 h 1.404307 z m 0,-1.933474 h -1.404307 v -1.404177 h 1.404307 z"
           inkscape:connector-curvature="0" />
      </g>
    </symbol>
    <symbol
       transform="translate(0.57970049,-3.2053384)"
       id="bedroom_symbol">
      <g transform="matrix(0.16493148,0,0,0.16493148,5.1689061,5.6506499)" >
        <path
           d="m 5.155325,14.096779 c 0.4289949,0 0.7864909,-0.3649 0.7864909,-0.802779 0,-0.456125 -0.357496,-0.802779 -0.7864909,-0.802779 -0.4289949,0 -0.7864906,0.3649 -0.7864906,0.802779 0,0.437879 0.3574957,0.802779 0.7864906,0.802779 z"
           inkscape:connector-curvature="0"
           style="display:inline;stroke-width:0.18058932" />
        <path
           d="m 12.090744,12.9291 c -0.08937,0 -0.178748,0.09122 -0.178748,0.18245 v 1.313638 H 11.679624 C 11.59025,13.585919 10.893133,12.9291 10.035143,12.9291 H 6.3529361 c -0.089374,0 -0.178748,0.09122 -0.178748,0.18245 v 1.313638 h -2.1271 v -3.028665 c 0,-0.09122 -0.089374,-0.18245 -0.178748,-0.18245 -0.089374,0 -0.1787477,0.09122 -0.1787477,0.18245 v 5.437001 c 0,0.10947 0.089374,0.18245 0.1787477,0.18245 0.089374,0 0.178748,-0.07298 0.178748,-0.18245 v -1.185923 h 7.8649079 v 1.185923 c 0,0.10947 0.08937,0.18245 0.178748,0.18245 0.08937,0 0.178747,-0.07298 0.178747,-0.18245 V 13.11155 c 0,-0.09122 -0.08937,-0.18245 -0.178747,-0.18245 z"
           inkscape:connector-curvature="0"
           style="display:inline;stroke-width:0.18058932" />
        <path
           style="stroke-width:0.26458332"
           d="m 3.4193901,17.862056 h 9.3725549 c 0.146244,0 0.264583,-0.118468 0.264583,-0.264584 V 8.7037 l 0.802018,0.5472533 c 0.04418,0.030102 0.09638,0.045992 0.149087,0.045992 0.01628,0 0.03281,-0.00156 0.04909,-0.00465 0.06899,-0.01292 0.129967,-0.052839 0.169499,-0.1108458 L 15.51064,7.2988771 C 15.59306,7.1782126 15.5618,7.0136232 15.44113,6.9311994 L 8.2547539,2.0276216 c -0.089917,-0.061236 -0.2082559,-0.061236 -0.2981729,0 L 0.77019782,6.9311983 C 0.64953327,7.0136221 0.61826905,7.1782117 0.7006931,7.298876 l 1.2844177,1.8825723 c 0.039532,0.058007 0.1005107,0.097927 0.1694987,0.1108459 0.06873,0.013049 0.1403014,-0.00206 0.198179,-0.041341 L 3.1548067,8.7036997 v 8.8937723 c 0,0.146116 0.1183392,0.264584 0.2645834,0.264584 z M 12.527361,17.332889 H 3.6839734 V 8.3426271 L 8.1056673,5.3254825 12.527361,8.3426271 Z M 2.2732068,8.6646843 1.2869621,7.2191652 8.1056673,2.5664776 14.924372,7.2191652 13.938128,8.6646843 8.2547539,4.7866266 c -0.044958,-0.030618 -0.096893,-0.045992 -0.1490866,-0.045992 -0.052193,0 -0.1041281,0.015372 -0.1490866,0.045992 z"
           inkscape:connector-curvature="0" />
      </g>
    </symbol>
    <symbol
       transform="translate(-11.499422,-0.19686141)"
       id="warehouse_symbol">
      <g
         transform="matrix(0.15083699,0,0,0.15083699,16.7668,2.5795169)">
        <path
           style="stroke-width:0.26458332"
           d="M 20.3277,17.923195 H 19.807318 V 9.716978 c 0,-0.019637 -0.0021,-0.039016 -0.0065,-0.058136 -0.710036,-3.1509703 -4.030246,-5.4381694 -7.89461,-5.4381694 -3.8643637,0 -7.1845744,2.2871991 -7.8946087,5.4381694 -0.00439,0.019121 -0.00646,0.038499 -0.00646,0.058136 v 8.206217 H 3.4848012 c -0.1462442,0 -0.2645834,0.11834 -0.2645834,0.264584 v 1.139465 c 0,0.146244 0.1183392,0.264584 0.2645834,0.264584 H 20.327701 c 0.146244,0 0.264583,-0.11834 0.264583,-0.264584 v -1.139465 c 0,-0.146244 -0.118339,-0.264584 -0.264584,-0.264584 z M 11.90625,4.7498392 c 3.483169,0 6.481355,1.9597962 7.287217,4.7025554 H 4.6190334 C 5.424895,6.7096357 8.4230808,4.7498392 11.90625,4.7498392 Z M 4.5343485,9.9815613 H 19.278151 V 17.923195 H 18.52135 v -6.928259 c 0,-0.146244 -0.118339,-0.264583 -0.264584,-0.264583 H 5.5557333 c -0.1462442,0 -0.2645834,0.118339 -0.2645834,0.264583 v 6.928259 H 4.5343485 Z M 15.279429,15.959491 h -1.69938 v -1.69938 c 0,-0.146244 -0.118339,-0.264583 -0.264583,-0.264583 h -1.963704 c -0.146245,0 -0.264584,0.118339 -0.264584,0.264583 v 1.963963 1.699121 h -0.325561 v -1.699121 -1.963963 -1.963704 c 0,-0.146244 -0.118339,-0.264583 -0.264584,-0.264583 H 8.5330705 c -0.1462442,0 -0.2645834,0.118339 -0.2645834,0.264583 v 1.963704 1.963963 1.699121 H 5.8203161 V 11.259519 H 17.992183 v 6.663676 h -2.448171 v -1.699121 c 0,-0.146244 -0.118339,-0.264583 -0.264583,-0.264583 z m -0.264583,0.529167 v 1.434537 h -1.434797 v -1.434537 z m -3.398501,-0.529167 v -1.434796 h 1.434538 v 1.434796 z m 1.434538,0.529167 v 1.434537 H 11.616345 V 16.488658 Z M 8.7976543,15.959491 v -1.434796 h 1.4347967 v 1.434796 z m 1.4347957,0.529167 v 1.434537 H 8.7976541 V 16.488658 Z M 8.7976543,13.995528 V 12.56099 h 1.4347967 v 1.434538 z M 20.063117,19.062661 H 3.7493834 v -0.610299 h 4.7836873 1.9639633 0.854728 1.963704 1.963963 4.783688 z"
           inkscape:connector-curvature="0" />
        <path
           style="stroke-width:0.26458332"
           d="M 14.021625,6.7424824 H 9.7908753 c -0.1462442,0 -0.2645833,0.1183391 -0.2645833,0.2645833 v 1.1048421 c 0,0.1462442 0.1183391,0.2645833 0.2645833,0.2645833 h 4.2307497 c 0.146244,0 0.264583,-0.1183391 0.264583,-0.2645833 V 7.0070657 c 0,-0.1462442 -0.118339,-0.2645833 -0.264583,-0.2645833 z M 13.757041,7.8473247 H 10.055459 V 7.2716493 h 3.701582 z"
           inkscape:connector-curvature="0" />
      </g>
    </symbol>
  </defs>
  <g
     style="display:inline;opacity:1"
     inkscape:groupmode="layer"
     inkscape:label="Base">
    <g
       inkscape:label="Key">
      <rect
         ry="1.5143965"
         y="270.42267"
         x="1.3041502"
         height="22.810596"
         width="18.369375"
         style="opacity:1;fill:#fffffd;fill-opacity:1;stroke:#000000;stroke-width:0.06246724;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" />
      <use
         height="100%"
         width="100%"
         y="0"
         x="0"
         xlink:href="#question_mark_symbol"
         transform="translate(-2.0905694,269.13794)" />
      <use
         height="100%"
         width="100%"
         y="0"
         x="0"
         xlink:href="#empty_square_symbol"
         transform="translate(-2.0934355,271.83872)" />
      <use
         height="100%"
         width="100%"
         y="0"
         x="0"
         xlink:href="#house_symbol"
         transform="translate(-2.1526894,274.88228)" />
      <use
         height="100%"
         width="100%"
         y="0"
         x="0"
         xlink:href="#bach_symbol"
         transform="translate(-2.3131108,277.47892)" />
      <use
         inkscape:transform-center-y="-0.28348214"
         inkscape:transform-center-x="1.0866815"
         height="100%"
         width="100%"
         y="0"
         x="0"
         xlink:href="#bach_in_sun_symbol"
         transform="translate(-2.188543,280.54401)" />
      <use
         height="100%"
         width="100%"
         y="0"
         x="0"
         xlink:href="#bedroom_symbol"
         transform="translate(-2.1298449,283.44567)" />
      <use
         height="100%"
         width="100%"
         y="0"
         x="0"
         xlink:href="#warehouse_symbol"
         transform="translate(-2.2412746,286.1392)" />
      <text
         inkscape:label="text25050"
         y="274.18185"
         x="6.7485552"
         style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:1.76388884px;line-height:1.60000002;font-family:'Liberation Serif';-inkscape-font-specification:'Liberation Serif, Normal';font-variant-ligatures:normal;font-variant-caps:normal;font-variant-numeric:normal;font-feature-settings:normal;text-align:start;letter-spacing:0px;word-spacing:0px;writing-mode:lr-tb;text-anchor:start;fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.26458332"
         xml:space="preserve"><tspan
           y="274.18185"
           x="6.7485552"
           sodipodi:role="line">unknown</tspan><tspan
           y="277.00409"
           x="6.7485552"
           sodipodi:role="line">Vacant</tspan><tspan
           y="279.82629"
           x="6.7485552"
           sodipodi:role="line">Permanent</tspan><tspan
           y="282.64853"
           x="6.7485552"
           sodipodi:role="line">Occasional</tspan><tspan
           y="285.47073"
           x="6.7485552"
           sodipodi:role="line">Holidays</tspan><tspan
           y="288.29297"
           x="6.7485552"
           sodipodi:role="line">Accommodation</tspan><tspan
           y="291.11517"
           x="6.7485552"
           sodipodi:role="line">Business</tspan></text>
    </g>
  </g>
  <g
     inkscape:groupmode="layer"
     inkscape:label="Addresses"
     style="display:inline">
  </g>
</svg>""".format(self.path.name, width, height)
        return xml

#-----------------------------------------------------------------------------
def makeDoc(csvPath, doc, clearStale=True):
    with open(csvPath, "r", newline='') as csvFile:
        csv = DictReader(csvFile)
        for row in csv:
            rapid = row.get('rapid')
            if not rapid or rapid.strip() == "":
                rowId = str(csv.line_num)
                names = row.get('names')
                if names is not None:
                    rowId += " ({})".format(names)
                print("Row {} has no RAPID, skipping.".format(rowId))
                continue
            doc.addAddress(row)
        if clearStale:
            doc.clearStaleAddresses()
        doc.save()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
