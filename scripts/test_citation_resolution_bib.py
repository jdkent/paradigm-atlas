"""Resolve silver/gold extraction citations against XML bibliographies (fallback EPMC). Runs on beast."""
import json, os, sys, glob, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.citations import resolve_with_bib, resolve, fetch_references
import taskcat.citations as C
C.CACHE = "data/cache/epmc_refs"
pas = {json.loads(l)["dbid"]: json.loads(l) for l in open(sys.argv[1])}
st = collections.Counter(); ex = []
for f in glob.glob(f"{sys.argv[2]}/*.json"):
    j = json.load(open(f)); d = j["dbid"]
    for t in (j.get("parsed") or {}).get("tasks") or []:
        for c in t.get("citations") or []:
            m = c.get("marker")
            if not m: continue
            st["cit"] += 1; st["role_" + str(c.get("role"))] += 1
            bp = f"data/bib/{d}.json"
            got, via = [], None
            if os.path.exists(bp):
                got = resolve_with_bib(m, json.load(open(bp))); via = "bib"
            if not got and os.path.exists(f"data/cache/epmc_refs/{pas[d]['pmid']}.json"):
                got = resolve(m, json.load(open(f"data/cache/epmc_refs/{pas[d]['pmid']}.json"))); via = "epmc"
            st["has_bib"] += os.path.exists(bp)
            if got:
                st["resolved"] += 1; st["via_" + via] += 1
                st["with_id"] += any(r.get("pmid") or r.get("doi") or r.get("id") for r in got)
            elif len(ex) < 15: ex.append((d, m, os.path.exists(bp)))
print(dict(st)); [print("UNRES", e) for e in ex]
