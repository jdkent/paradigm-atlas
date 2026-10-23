"""Convert JATS XML body to markdown-ish text (## headings by section depth), same convention as pubget text.txt."""
from lxml import etree

def _t(el):
    return " ".join("".join(el.itertext()).split())

def jats_to_text(xml_bytes):
    root = etree.fromstring(xml_bytes, etree.XMLParser(recover=True, huge_tree=True))
    out = []
    title = root.find(".//article-meta//article-title")
    if title is not None:
        out.append("# " + _t(title) + "\n")
    ab = root.find(".//article-meta/abstract")
    if ab is not None:
        out.append("## Abstract\n\n" + _t(ab) + "\n")
    body = root.find(".//body")
    if body is None:
        return "\n".join(out)
    def walk(el, depth):
        for c in el:
            tag = c.tag if isinstance(c.tag, str) else ""
            if tag == "sec":
                t = c.find("title")
                if t is not None:
                    out.append("#" * min(6, depth + 1) + " " + _t(t) + "\n")
                walk(c, depth + 1)
            elif tag in ("p", "list"):
                out.append(_t(c) + "\n")
            elif tag in ("table-wrap", "fig"):
                cap = c.find(".//caption")
                if cap is not None:
                    out.append(_t(cap) + "\n")
            elif tag not in ("title",):
                walk(c, depth)
    walk(body, 1)
    return "\n".join(out)
