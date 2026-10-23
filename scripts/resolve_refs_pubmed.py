"""DOI/title -> PMID for task-cited refs lacking PMIDs (PubMed esearch, API key). Output: data/ref_pmid_map.json"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat import pubmed as P
P.load_env()
refs = json.load(open(sys.argv[1])); out = sys.argv[2]
done = json.load(open(out)) if os.path.exists(out) else {}
def key(r): return (r.get("doi") or "").lower() or "t:" + (r.get("title") or "")[:120].lower()
def go(r):
    k = key(r)
    if k in done: return k, done[k]
    pm = P.doi_to_pmid(r["doi"]) if r.get("doi") else None
    if not pm and r.get("title"):
        fa = (r.get("first_author") or "").split()[0] if r.get("first_author") else None
        pm = P.title_to_pmid(r["title"], fa, r.get("year"))
    return k, pm
with ThreadPoolExecutor(4) as ex:
    for i, (k, pm) in enumerate(ex.map(go, refs)):
        done[k] = pm
        if i % 500 == 0: json.dump(done, open(out, "w")); print(i, sum(1 for v in done.values() if v), flush=True)
json.dump(done, open(out, "w")); print("resolved", sum(1 for v in done.values() if v), "of", len(done))
