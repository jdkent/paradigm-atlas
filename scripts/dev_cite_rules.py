"""Rule precision on Luna TRAINING silver only (no astra). Usage: dev_cite_rules.py PASSAGES SILVER_DIR"""
import json, os, sys, glob, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.cite_roles import citing_sentence, rule_hits, surname
from taskcat.citations import resolve_with_bib
pas = {json.loads(l)["dbid"]: json.loads(l) for l in open(sys.argv[1])}
pm = {}
for f in glob.glob("data/pubmed*/meta_*.jsonl"):
    for l in open(f):
        r = json.loads(l); pm[r["pmid"]] = r
hits = collections.defaultdict(collections.Counter); roles = collections.Counter(); self_c = collections.Counter()
n = 0
for f in glob.glob(os.path.join(sys.argv[2], "*.json")):
    j = json.load(open(f)); P = pas.get(j["dbid"])
    if not P or not j.get("parsed"): continue
    bp = f"data/bib/{j['dbid']}.json"; bib = json.load(open(bp)) if os.path.exists(bp) else None
    auth = [a.get("last") for a in (pm.get(P.get("pmid")) or {}).get("authors", [])]
    for t in j["parsed"].get("tasks") or []:
        for c in t.get("citations") or []:
            m, role = c.get("marker"), c.get("role")
            if isinstance(role, list): role = role[0] if role else None
            if not m or not role: continue
            s = citing_sentence(P["passage"], m)
            if not s: continue
            n += 1; roles[role] += 1
            for r, name in rule_hits(s): hits[name][role] += 1
            if bib and auth:
                got = resolve_with_bib(m, bib)
                if got and surname(got[0].get("first_author")) in {surname(a) for a in auth}:
                    self_c[role] += 1
print("citations with sentence:", n, dict(roles))
from taskcat.cite_roles import RULES
target = {name: r for r, name, _ in RULES}
for name, cnt in sorted(hits.items()):
    tot = sum(cnt.values()); r = target[name]
    print(f"{name:14s} -> {r:15s} hits {tot:4d} precision {cnt[r]/max(1,tot):.3f}  lineage-agree {sum(cnt[k] for k in ('task_origin','adapted_from','prior_use'))/max(1,tot):.3f}  {dict(cnt.most_common(4))}")
tot = sum(self_c.values())
print(f"self_citation   -> prior_use       hits {tot:4d} precision {self_c['prior_use']/max(1,tot):.3f}  lineage {sum(self_c[k] for k in ('task_origin','adapted_from','prior_use'))/max(1,tot):.3f} {dict(self_c.most_common(4))}")
