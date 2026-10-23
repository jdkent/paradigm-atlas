"""Assemble TaskCards from TaskMention extractions (v1 single-pass or v2 two-pass outputs).
Usage (beast): build_taskcards.py PASSAGES EXTRACTION_DIR OUT.jsonl"""
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.validate import clean
from taskcat.template import to_v2
from taskcat.cards import CardBuilder
CB = CardBuilder()
pas = {json.loads(l)["dbid"]: json.loads(l) for l in open(sys.argv[1])}
pm = {}
for f in glob.glob("data/pubmed*/meta_*.jsonl"):
    for l in open(f):
        r = json.loads(l); pm[r["pmid"]] = r
out = open(sys.argv[3], "w"); n = 0
for f in sorted(glob.glob(os.path.join(sys.argv[2], "*.json"))):
    j = json.load(open(f)); d = j["dbid"]; P = pas.get(d)
    if P is None or j.get("parsed") is None: continue
    obj = to_v2(clean(j["parsed"], P["passage"]))
    bp = f"data/bib/{d}.json"
    if not os.path.exists(bp): bp = f"data/psych/{d}/bib.json"
    bib = json.load(open(bp)) if os.path.exists(bp) else None
    ep = f"data/cache/epmc_refs/{P.get('pmid')}.json"
    epmc = json.load(open(ep)) if not bib and os.path.exists(ep) else None
    meta = pm.get(P.get("pmid")) or {}
    paper = {"dbid": d, "pmid": P.get("pmid"), "pmcid": P.get("pmcid"), "doi": P.get("doi"),
             "year": meta.get("year") or P.get("year"), "journal": meta.get("journal") or P.get("journal"),
             "title": meta.get("title") or P.get("title"), "corpus": "psych" if d.startswith("PMC") else "ns-pond"}
    for i, t in enumerate(obj.get("tasks") or []):
        card = CB.build(t, {**paper, "instance_id": f"{d}#{i}"}, bib, epmc, meta.get("authors"))
        out.write(json.dumps(card, ensure_ascii=False) + "\n"); n += 1
print("cards", n)
