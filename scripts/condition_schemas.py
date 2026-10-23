"""Normalize all TE conditions; derive per-canonical-task condition schemas (axes x levels, phases, kinds)."""
import json, collections, sys
sys.path.insert(0, '.')
from taskcat.conditions import normalize_condition_ctx
from taskcat.lexicon import Lexicon
L = Lexicon()
rows = {r['mid']: r for r in map(json.loads, open('data/taskextractor/te_tasks.jsonl')) if r['kind'] != 'none'}
N = {r['mid']: r for r in map(json.loads, open('data/taskextractor/te_normalized.jsonl'))}
tot = cov = 0; per = collections.defaultdict(lambda: {"n_mentions": 0, "n_conds": 0, "atoms": collections.Counter(),
                    "axes": collections.defaultdict(collections.Counter), "phases": collections.Counter(), "kinds": collections.Counter(),
                    "residue": collections.Counter(), "names": collections.Counter()})
out = open('data/taskextractor/te_conditions_normalized.jsonl', 'w')
for mid, r in rows.items():
    conds = [c if isinstance(c, str) else (c.get('name') if isinstance(c, dict) else str(c)) for c in (r.get('Conditions') or [])]
    lab = (N.get(mid) or {}).get('canonical')
    normed = [normalize_condition_ctx(c, lab, (L.family.get(lab) or [None])[0] if lab else None) for c in conds if c]
    out.write(json.dumps({"mid": mid, "canonical": lab, "conditions": normed}) + "\n")
    if lab: per[lab]["n_mentions"] += 1
    for c in normed:
        tot += 1; cov += bool(c['atoms'] or c['phases'] or c['kind'] != 'task_state')
        if not lab: continue
        P = per[lab]; P["n_conds"] += 1; P["kinds"][c['kind']] += 1
        for a in c['atoms']:
            P["atoms"][a] += 1; ax, v = a.split(':'); P["axes"][ax][v] += 1
        for ph in c['phases']: P["phases"][ph] += 1
        if c['residue']: P["residue"][c['residue']] += 1
        P["names"][c['name'].lower()] += 1
print(f"conditions {tot}, with >=1 atom/phase/non-default kind {cov/tot:.3f}")
schemas = []
for k, P in sorted(per.items(), key=lambda kv: -kv[1]['n_mentions']):
    if P['n_mentions'] < 10: continue
    m = P['n_mentions']
    axes = {ax: [(v, c) for v, c in vs.most_common(6)] for ax, vs in P['axes'].items()
            if sum(vs.values()) / m >= 0.15}       # an axis is part of the schema if it appears in >=15% of mentions
    schemas.append({"task": k, "name": L.names.get(k), "mentions": m, "conds_per_mention": round(P['n_conds'] / m, 2),
                    "axes": axes, "phases": P['phases'].most_common(5), "kinds": P['kinds'].most_common(),
                    "top_condition_names": P['names'].most_common(12), "top_residue": P['residue'].most_common(10)})
json.dump(schemas, open('data/taskextractor/condition_schemas.json', 'w'), indent=1)
for s in schemas[:22]:
    ax = "; ".join(f"{a}={'/'.join(v for v, _ in vs[:4])}" for a, vs in sorted(s['axes'].items(), key=lambda kv: -sum(c for _, c in kv[1])))
    print(f"{s['name'][:30]:30s} n={s['mentions']:4d} | {ax[:110]} | phases {[p for p,_ in s['phases'][:3]]}")
