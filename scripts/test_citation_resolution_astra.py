"""Resolve the verbatim task `references` in the 100 astra records against Europe PMC bibliographies."""
import json, glob, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.citations import fetch_references, resolve
RUN = "/home/jdkent/projects/StudyIESchema/pondie/pubget-astra-medium-100-results-20261008/runs/pubget_astra_medium_100"
stats = collections.Counter(); rows = []
for f in sorted(glob.glob(f"{RUN}/records/*.extraction.json")):
    dbid = os.path.basename(f).split(".")[0]
    ids = json.load(open(f"{RUN}/corpus/{dbid}/identifiers.json"))
    rec = json.load(open(f))
    for t in rec.get("tasks") or []:
        cits = (t.get("references") or {}).get("value") or []
        if not cits: continue
        refs = fetch_references(ids["pmid"])
        stats["papers_refs_ok" if refs else "papers_refs_missing"] += 1
        for c in cits:
            m = resolve(c, refs)
            stats["cit"] += 1; stats["cit_resolved"] += bool(m)
            stats["cit_resolved_pmid"] += bool(m and any(x.get("id") for x in m))
            rows.append({"dbid": dbid, "task": t["name"]["value"], "citation": c,
                         "resolved": [(x.get("id"), x.get("authorString", "")[:30], x.get("pubYear"), (x.get("title") or "")[:70]) for x in m]})
print(stats)
for r in rows: print(json.dumps(r, ensure_ascii=False)[:400])
