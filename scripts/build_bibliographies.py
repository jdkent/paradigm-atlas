"""Parse reference lists for all ns-pond papers with JATS or Elsevier XML. Output: data/bib/<dbid>.json (runs on beast)."""
import json, os, sys, glob
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.bibliography import parse_jats, parse_elsevier
D = "/data/alejandro/projects/ns-pond/data"; OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
def one(dbid):
    o = os.path.join(OUT, dbid + ".json")
    if os.path.exists(o): return "skip"
    src = os.path.join(D, dbid, "source")
    for sub, fn in (("pubget", parse_jats), ("pmc", parse_jats), ("elsevier", parse_elsevier)):
        p = os.path.join(src, sub)
        if not os.path.isdir(p): continue
        cands = [f for f in glob.glob(os.path.join(p, "*.xml")) if not f.endswith("tables.xml")]
        cands.sort(key=lambda f: (os.path.basename(f) != "article.xml" and sub != "elsevier", f))
        for f in cands:
            try:
                b = fn(f)
            except Exception as e:
                continue
            if b["refs"]:
                b["file"] = f; json.dump(b, open(o, "w")); return sub
    return "none"
if __name__ == "__main__":
    ids = [json.loads(l)["dbid"] for l in open(sys.argv[1])]
    import collections; C = collections.Counter()
    with ProcessPoolExecutor(24) as ex:
        for r in ex.map(one, ids, chunksize=50): C[r] += 1
    print(C)
