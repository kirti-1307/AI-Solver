"""Build Assignment2_Report.docx from report.html (standard library only).

    python report/build_report.py

report.html is the single source of the report text. This script converts
the small set of HTML tags it uses (h1, h2, p, ul/li, table, b, i, sub, sup,
br, img and two classes) into a Word document, so the report can be edited
in one place and rebuilt.
"""

from __future__ import annotations

import os
import re
import struct
import zipfile
from html.parser import HTMLParser
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "report.html")
OUTPUT = os.path.join(HERE, "Assignment2_Report.docx")

# A4 page and margins, in twentieths of a point
PAGE_W, PAGE_H = 11906, 16838
M_TOP, M_BOTTOM, M_SIDE = 700, 660, 840
TEXT_W = PAGE_W - 2 * M_SIDE
FONT = "Calibri"
BASE_SIZE = 20            # half-points: 10 pt
BLUE = "0B3D73"

STYLES = {
    # name: (size half-pt, bold, colour, space before, space after, justify, keep with next)
    "h1": (32, True, BLUE, 0, 20, "left", True),
    "meta": (18, False, "333333", 0, 90, "left", False),
    "h2": (22, True, BLUE, 110, 40, "left", True),
    "p": (BASE_SIZE, False, None, 0, 70, "both", False),
    "li": (BASE_SIZE, False, None, 0, 44, "both", False),
    "cell": (18, False, None, 0, 0, "left", False),
    "cap": (17, False, "333333", 20, 60, "left", False),
    "fig": (BASE_SIZE, False, None, 40, 0, "center", True),
}


def run_xml(text: str, fmt: dict, size: int, bold: bool, colour) -> str:
    props = [f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/>']
    if bold or fmt.get("b"):
        props.append("<w:b/>")
    if fmt.get("i"):
        props.append("<w:i/>")
    if colour:
        props.append(f'<w:color w:val="{colour}"/>')
    props.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    if fmt.get("fill"):
        props.append('<w:shd w:val="clear" w:color="auto" w:fill="FFF2A8"/>')
    if fmt.get("sub"):
        props.append('<w:vertAlign w:val="subscript"/>')
    if fmt.get("sup"):
        props.append('<w:vertAlign w:val="superscript"/>')
    body = "<w:br/>" if text == "\n" else f'<w:t xml:space="preserve">{escape(text)}</w:t>'
    return f"<w:r><w:rPr>{''.join(props)}</w:rPr>{body}</w:r>"


def para_xml(runs, style: str, bullet: bool = False) -> str:
    size, bold, colour, before, after, align, keep = STYLES[style]
    ppr = [f'<w:spacing w:before="{before}" w:after="{after}" w:line="259" w:lineRule="auto"/>']
    if bullet:
        ppr.append('<w:ind w:left="250" w:hanging="190"/>')
    ppr.append(f'<w:jc w:val="{align}"/>')
    if keep:
        ppr.insert(0, "<w:keepNext/>")
    out = []
    if bullet:
        out.append(run_xml("• ", {}, size, False, colour))
    for text, fmt in runs:
        out.append(run_xml(text, fmt, size, bold, colour))
    return f"<w:p><w:pPr>{''.join(ppr)}</w:pPr>{''.join(out)}</w:p>"


def table_xml(rows) -> str:
    first = rows[0]
    pct = first[0]["width"] or 25
    widths = [round(TEXT_W * pct / 100)]
    rest = len(first) - 1
    widths += [round((TEXT_W - widths[0]) / rest)] * rest
    border = "".join(
        f'<w:{side} w:val="single" w:sz="6" w:space="0" w:color="9AA5B1"/>'
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"))
    xml = [
        "<w:tbl><w:tblPr>",
        f'<w:tblW w:w="{TEXT_W}" w:type="dxa"/><w:tblBorders>{border}</w:tblBorders>',
        '<w:tblLayout w:type="fixed"/>',
        '<w:tblCellMar><w:top w:w="20" w:type="dxa"/><w:left w:w="80" w:type="dxa"/>'
        '<w:bottom w:w="20" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar>',
        "</w:tblPr><w:tblGrid>",
        "".join(f'<w:gridCol w:w="{w}"/>' for w in widths),
        "</w:tblGrid>",
    ]
    for row in rows:
        xml.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>')
        for cell, width in zip(row, widths):
            shade = '<w:shd w:val="clear" w:color="auto" w:fill="E6EEF7"/>' if cell["head"] else ""
            runs = [(t, dict(f, b=f.get("b") or cell["head"])) for t, f in cell["runs"]]
            xml.append(f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shade}</w:tcPr>'
                       f'{para_xml(runs, "cell")}</w:tc>')
        xml.append("</w:tr>")
    xml.append("</w:tbl>")
    # Word needs a paragraph after a table; make it tiny
    xml.append('<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="60" w:lineRule="exact"/></w:pPr></w:p>')
    return "".join(xml)


def png_size(path: str):
    with open(path, "rb") as fh:
        head = fh.read(24)
    return struct.unpack(">II", head[16:24])


def image_xml(rel_id: str, path: str, width_in: float) -> str:
    w_px, h_px = png_size(path)
    cx = int(width_in * 914400)
    cy = int(cx * h_px / w_px)
    drawing = (
        f'<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
        '<wp:docPr id="1" name="Figure" descr="Product slate and electrochemical lens results"/>'
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:nvPicPr><pic:cNvPr id="1" name="figure.png"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
        "</a:graphicData></a:graphic></wp:inline></w:drawing>")
    size, _, _, before, after, align, _ = STYLES["fig"]
    return (f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="{before}" w:after="{after}"/><w:jc w:val="{align}"/></w:pPr>'
            f"<w:r>{drawing}</w:r></w:p>")


class Converter(HTMLParser):
    BLOCKS = {"h1": "h1", "h2": "h2", "p": "p", "li": "li"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.body = []
        self.runs = None          # runs of the open block, or None
        self.style = None
        self.fmt = {}
        self.fmt_stack = []
        self.table = None
        self.row = None
        self.cell = None
        self.images = []
        self.in_body = False
        self.words = 0

    # -- helpers ---------------------------------------------------------------
    def _open(self, style):
        self.runs, self.style = [], style

    def _clean(self, runs):
        """Collapse HTML whitespace the way a browser would."""
        out = []
        for text, fmt in runs:
            if text == "\n":
                if out and out[-1][0] != "\n":
                    out[-1] = (out[-1][0].rstrip(" "), out[-1][1])
                out.append((text, fmt))
                continue
            text = re.sub(r"\s+", " ", text)
            at_line_start = not out or out[-1][0] == "\n"
            after_space = bool(out) and out[-1][0].endswith(" ")
            if at_line_start or after_space:
                text = text.lstrip(" ")
            if text:
                out.append((text, fmt))
        while out and (out[-1][0] == "\n" or not out[-1][0].strip()):
            out.pop()
        if out:
            out[-1] = (out[-1][0].rstrip(" "), out[-1][1])
        return [r for r in out if r[0]]

    def _close(self):
        runs = self._clean(self.runs or [])
        self.words += sum(len(t.split()) for t, _ in runs)
        style, self.runs, self.style = self.style, None, None
        return runs, style

    # -- parser callbacks --------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "body":
            self.in_body = True
        if not self.in_body:
            return
        if tag in self.BLOCKS:
            style = self.BLOCKS[tag]
            if tag == "p" and a.get("class") in ("meta", "cap"):
                style = a["class"]
            self._open(style)
        elif tag == "table":
            self.table = []
        elif tag == "tr":
            self.row = []
        elif tag in ("th", "td"):
            m = re.search(r"width:\s*(\d+)%", a.get("style", ""))
            self.cell = {"head": tag == "th", "width": int(m.group(1)) if m else None}
            self._open("cell")
        elif tag in ("b", "i", "sub", "sup", "span"):
            self.fmt_stack.append(dict(self.fmt))
            key = "fill" if tag == "span" and a.get("class") == "fill" else tag
            if key != "span":
                self.fmt = dict(self.fmt, **{key: True})
        elif tag == "br" and self.runs is not None:
            self.runs.append(("\n", {}))
        elif tag == "img":
            self.images.append(os.path.join(HERE, a["src"]))
            self.body.append(image_xml(f"rIdImg{len(self.images)}", self.images[-1], 6.95))
            self.runs = None

    def handle_endtag(self, tag):
        if not self.in_body:
            return
        if tag in self.BLOCKS and self.runs is not None:
            runs, style = self._close()
            if runs:
                self.body.append(para_xml(runs, style, bullet=(tag == "li")))
        elif tag in ("th", "td"):
            runs, _ = self._close()
            self.cell["runs"] = runs
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr":
            self.table.append(self.row)
            self.row = None
        elif tag == "table":
            self.body.append(table_xml(self.table))
            self.table = None
        elif tag in ("b", "i", "sub", "sup", "span") and self.fmt_stack:
            self.fmt = self.fmt_stack.pop()
        elif tag == "body":
            self.in_body = False

    def handle_data(self, data):
        if self.in_body and self.runs is not None:
            self.runs.append((data, dict(self.fmt)))


W_NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"')


def build() -> int:
    with open(SOURCE, encoding="utf-8") as fh:
        html = fh.read()
    conv = Converter()
    conv.feed(html)

    sect = (f'<w:sectPr><w:pgSz w:w="{PAGE_W}" w:h="{PAGE_H}"/>'
            f'<w:pgMar w:top="{M_TOP}" w:right="{M_SIDE}" w:bottom="{M_BOTTOM}" w:left="{M_SIDE}" '
            'w:header="340" w:footer="340" w:gutter="0"/></w:sectPr>')
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W_NS}><w:body>'
                f'{"".join(conv.body)}{sect}</w:body></w:document>')
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults>'
        f'<w:rPrDefault><w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}" w:eastAsia="{FONT}"/>'
        f'<w:sz w:val="{BASE_SIZE}"/><w:szCs w:val="{BASE_SIZE}"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault>'
        '<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr></w:pPrDefault>'
        '</w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
        '</w:styles>')
    rels = "".join(
        f'<Relationship Id="rIdImg{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
        f'Target="media/image{i}.png"/>' for i in range(1, len(conv.images) + 1))
    doc_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
                f'Target="styles.xml"/>{rels}</Relationships>')
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '</Types>')
    root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                 'Target="word/document.xml"/></Relationships>')

    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", styles)
        z.writestr("word/_rels/document.xml.rels", doc_rels)
        for i, path in enumerate(conv.images, 1):
            z.write(path, f"word/media/image{i}.png")
    return conv.words


if __name__ == "__main__":
    words = build()
    print(f"wrote {OUTPUT} ({words} words)")
