"""Manifest of ns-pond papers: ids, metadata, available text sources, heading counts. Runs on beast."""
import json, os, re, sys
from concurrent.futures import ProcessPoolExecutor
D = "/data/alejandro/projects/ns-pond/data"
PREF = ["pubget", "pmc", "elsevier", "ace", "pdf"]
def one(dbid):
    p = os.path.join(D, dbid)
    try:
        ids = json.load(open(os.path.join(p, "identifiers.json")))
    except Exception:
        ids = {}
    row = {"dbid": dbid, "pmid": ids.get("pmid"), "pmcid": ids.get("pmcid"), "doi": ids.get("doi"), "sources": {}}
    try:
        m = json.load(open(os.path.join(p, "processed/db/metadata.json")))
        row.update(title=m.get("title"), authors=m.get("authors"), journal=m.get("journal"), year=m.get("publication_year"))
    except Exception:
        pass
    proc = os.path.join(p, "processed")
    for src in (os.listdir(proc) if os.path.isdir(proc) else []):
        t = os.path.join(proc, src, "text.txt")
        if os.path.exists(t):
            try:
                txt = open(t, errors="replace").read()
            except Exception:
                continue
            row["sources"][src] = {"len": len(txt), "md_headings": len(re.findall(r"(?m)^#{1,6} ", txt)),
                                   "has_refs": bool(re.search(r"(?mi)^#*\s*references\s*$", txt))}
            if "title" not in row or not row.get("authors"):
                try:
                    m = json.load(open(os.path.join(proc, src, "metadata.json")))
                    row.setdefault("title", m.get("title")); row["authors"] = row.get("authors") or m.get("authors")
                    row["journal"] = row.get("journal") or m.get("journal")
                except Exception:
                    pass
    srcd = os.path.join(p, "source")
    row["raw"] = sorted(os.listdir(srcd)) if os.path.isdir(srcd) else []
    best = [s for s in PREF if s in row["sources"] and row["sources"][s]["len"] > 2000]
    row["best_source"] = best[0] if best else None
    return row
if __name__ == "__main__":
    ids = sorted(os.listdir(D))
    with ProcessPoolExecutor(16) as ex, open(sys.argv[1], "w") as fo:
        for r in ex.map(one, ids, chunksize=200):
            fo.write(json.dumps(r) + "\n")
