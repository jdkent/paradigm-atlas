"""Citation-role accuracy on matched citations (task-aligned, marker-normalized), with optional rules.
Usage: eval_cit_roles.py PASSAGES REF_DIR PRED_DIR"""
import json, os, sys, glob, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.evaluate import load_dir, align, cit_norm
from taskcat.validate import clean
from taskcat.cite_roles import citing_sentence, apply_rules
from taskcat.citations import resolve_with_bib
pas = {json.loads(l)["dbid"]: json.loads(l) for l in open(sys.argv[1])}
R, P = load_dir(sys.argv[2]), load_dir(sys.argv[3])
pm = {}
for f in glob.glob("data/pubmed*/meta_*.jsonl"):
    for l in open(f):
        r = json.loads(l); pm[r["pmid"]] = r
KEEP = {"taken_from", "named_set", "software", "database", "programmed", "previous"}
LIN = {"task_origin", "adapted_from", "prior_use"}
def r1(x): return (x[0] if x else None) if isinstance(x, list) else x
POL = {"model_only": None, "override_kept": ("override", KEEP), "fill_kept": ("fill", KEEP),
       "override_kept+self": ("override", KEEP | {"self_citation"}), "fill_kept+self": ("fill", KEEP | {"self_citation"})}
res = {k: collections.Counter() for k in POL}
for d in R:
    if d not in P: continue
    passage = pas[d]["passage"]
    rt = clean(R[d], passage)["tasks"]; pt = clean(P[d], passage)["tasks"]
    bp = f"data/bib/{d}.json"
    if not os.path.exists(bp): bp = f"data/psych/{d}/bib.json"
    bib = json.load(open(bp)) if os.path.exists(bp) else None
    auth = [a.get("last") for a in (pm.get(pas[d].get("pmid")) or {}).get("authors", [])]
    for i, j in align(pt, rt):
        refc = {cit_norm(c.get("marker")): r1(c.get("role")) for c in rt[j].get("citations") or [] if c.get("marker")}
        for c in pt[i].get("citations") or []:
            m = c.get("marker"); k = cit_norm(m)
            if not m or k not in refc or not refc[k]: continue
            gold = refc[k]; s = citing_sentence(passage, m)
            fa = None
            if bib:
                got = resolve_with_bib(m, bib); fa = got[0].get("first_author") if got else None
            for name, pol in POL.items():
                pred = r1(c.get("role")) if pol is None else apply_rules(r1(c.get("role")), s, fa, auth, enabled=pol[1], policy=pol[0])[0]
                C = res[name]; C["n"] += 1; C["acc"] += pred == gold
                C["bin"] += (pred in LIN) == (gold in LIN)
                C["tp"] += pred in LIN and gold in LIN; C["pp"] += pred in LIN; C["gp"] += gold in LIN
for name, C in res.items():
    p = C["tp"] / max(1, C["pp"]); r = C["tp"] / max(1, C["gp"])
    print(f"{name:20s} n={C['n']:4d}  role acc {C['acc']/max(1,C['n']):.3f}  lineage-vs-other acc {C['bin']/max(1,C['n']):.3f}  lineage P {p:.3f} R {r:.3f} F1 {2*p*r/max(1e-9,p+r):.3f}")
