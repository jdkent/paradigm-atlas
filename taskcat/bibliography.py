"""Per-paper bibliography from local full-text XML (JATS / Elsevier), with explicit in-text marker -> reference links.

Output: {"source": "jats"|"elsevier", "refs": [{"rid", "order", "first_author", "authors", "year", "title",
         "journal", "doi", "pmid", "pmcid"}], "xrefs": [{"text", "rids"}]}
"""
import re
from lxml import etree

_YEAR = re.compile(r"(1[89]\d\d|20\d\d)")


def _t(el):
    return " ".join("".join(el.itertext()).split()) if el is not None else None


def _local(tag):
    return tag.split("}")[-1] if isinstance(tag, str) else ""


def parse_jats(path):
    tree = etree.parse(path, etree.XMLParser(recover=True, huge_tree=True))
    refs = []
    for i, ref in enumerate(tree.iter("ref"), 1):
        cit = next((c for c in ref if _local(c.tag) in ("mixed-citation", "element-citation", "citation", "nlm-citation")), None)
        if cit is None:
            cit = ref
        surnames = [_t(s) for s in cit.iter("surname")]
        year = _t(cit.find(".//year"))
        if not year:
            m = _YEAR.search(_t(cit) or ""); year = m.group(1) if m else None
        ids = {p.get("pub-id-type"): _t(p) for p in cit.iter("pub-id")}
        doi = ids.get("doi")
        if not doi:
            m = re.search(r"10\.\d{4,9}/[^\s\"<>]+", _t(cit) or ""); doi = m.group(0).rstrip(".") if m else None
        refs.append({"rid": ref.get("id"), "order": i, "first_author": surnames[0] if surnames else None,
                     "authors": surnames[:8], "year": (year or "")[:4] or None,
                     "title": _t(cit.find(".//article-title")) or _t(cit.find(".//chapter-title")) or _t(cit.find(".//source")),
                     "journal": _t(cit.find(".//source")), "doi": doi, "pmid": ids.get("pmid"), "pmcid": ids.get("pmcid"),
                     "raw": (_t(cit) or "")[:400]})
    xrefs = []
    for x in tree.iter("xref"):
        if x.get("ref-type") == "bibr" and x.get("rid"):
            xrefs.append({"text": _t(x), "rids": x.get("rid").split()})
    return {"source": "jats", "refs": refs, "xrefs": xrefs}


def parse_elsevier(path):
    tree = etree.parse(path, etree.XMLParser(recover=True, huge_tree=True))
    refs = []
    for i, br in enumerate((e for e in tree.iter() if _local(e.tag) == "bib-reference"), 1):
        sur = [_t(s) for s in br.iter() if _local(s.tag) == "surname"]
        year = next((_t(e) for e in br.iter() if _local(e.tag) in ("date", "year")), None)
        if year:
            m = _YEAR.search(year); year = m.group(1) if m else None
        title = next((_t(e) for e in br.iter() if _local(e.tag) == "maintitle"), None)
        journal = next((_t(e) for e in br.iter() if _local(e.tag) == "title" and e is not None and
                        _local(e.getparent().tag) == "sb:series"), None)
        doi = next((_t(e) for e in br.iter() if _local(e.tag) == "doi"), None)
        raw = _t(br) or ""
        if not year:
            m = _YEAR.search(raw); year = m.group(1) if m else None
        refs.append({"rid": br.get("id"), "order": i, "first_author": sur[0] if sur else None, "authors": sur[:8],
                     "year": year, "title": title, "journal": journal, "doi": doi, "pmid": None, "pmcid": None,
                     "raw": raw[:400]})
    xrefs = []
    for x in tree.iter():
        if _local(x.tag) in ("cross-ref", "cross-refs") and x.get("refid"):
            rids = x.get("refid").split()
            if any(r.startswith(("bib", "b", "ref", "BIB")) for r in rids):
                xrefs.append({"text": _t(x), "rids": rids})
    return {"source": "elsevier", "refs": refs, "xrefs": xrefs}
