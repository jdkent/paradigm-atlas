"""H8: corpus citation patterns rediscover each paradigm's origin paper.
For each canonical task: refs cited near its mentions, ranked by (papers citing it for this task) x purity.
Compare top refs to hed-task curated references (DOI/PMID/first-author+year)."""
import json, collections, sys, math, re
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
L = Lexicon()
N = {r['mid']: r for r in map(json.loads, open('data/taskextractor/te_normalized.jsonl'))}
import pickle, os
cit = [json.loads(l) for l in open('data/taskextractor/te_citations_ctx.jsonl')]
THR = float(os.environ.get('PLIN', 0))
if THR > 0:
    vec, clf = pickle.load(open('data/citation_role_lineage_clf.pkl', 'rb')); li = list(clf.classes_).index('lineage')
    ctx = [x.get('context') or '' for c in cit for x in c['refs']]
    pr = clf.predict_proba(vec.transform(ctx))[:, li]; i = 0
    for c in cit:
        keep = []
        for x in c['refs']:
            if pr[i] >= THR: keep.append(x)
            i += 1
        c['refs'] = keep
def rkey(x):
    if x.get('doi'): return 'doi:' + x['doi'].lower().strip()
    if x.get('pmid'): return 'pmid:' + str(x['pmid'])
    fa = (x.get('first_author') or '').strip().lower(); t = (x.get('title') or '')[:50].lower()
    return f'ay:{fa}:{x.get("year")}:{t}' if fa and x.get('year') and len(t) > 10 else None
by_ref = collections.defaultdict(lambda: collections.defaultdict(set)); info = {}
for c in cit:
    lab = (N.get(c.get('mid')) or {}).get('canonical')
    for x in c['refs']:
        k = rkey(x)
        if not k: continue
        by_ref[k][lab].add(c['dbid']); info[k] = x
task_refs = collections.defaultdict(list)
for k, d in by_ref.items():
    tot = sum(len(v) for v in d.values())
    for lab, ps in d.items():
        if lab and lab != 'hedtsk_rest' and len(ps) >= 3:
            purity = len(ps) / tot
            task_refs[lab].append((len(ps) * purity, len(ps), purity, k))
# curated origins from hed-task references
cur = collections.defaultdict(set)
for k, t in L.tasks.items():
    for r in t.get('references') or []:
        ids = r.get('ids') or {}
        if ids.get('doi'): cur[k].add('doi:' + ids['doi'].lower())
        if ids.get('pmid'): cur[k].add('pmid:' + str(ids['pmid']))
        au = (r.get('authors') or '').split(',')[0].strip().lower()
        if au and r.get('year'): cur[k].add(f"ay:{au}:{r['year']}")
def matches(k, x, curset):
    if k in curset: return True
    fa = (x.get('first_author') or '').lower().strip(); y = str(x.get('year'))
    return f"ay:{fa}:{y}" in curset
hit1 = hit5 = n = 0; report = []
for lab, lst in sorted(task_refs.items(), key=lambda kv: -sum(x[1] for x in kv[1])):
    lst.sort(reverse=True)
    top = lst[:5]
    if lab in cur and cur[lab]:
        n += 1
        h = [matches(k, info[k], cur[lab]) for _, _, _, k in top]
        hit1 += h[0] if h else 0; hit5 += any(h)
    report.append({"task": lab, "name": L.names.get(lab), "top_refs": [
        {"papers": c, "purity": round(p, 2), "first_author": info[k].get('first_author'), "year": info[k].get('year'),
         "title": (info[k].get('title') or '')[:90], "pmid": info[k].get('pmid'), "doi": info[k].get('doi'),
         "curated": matches(k, info[k], cur.get(lab, set()))} for s, c, p, k in top]})
print(f"tasks with curated refs & corpus refs: {n}; top-1 is a curated ref: {hit1/n:.3f}; curated ref in top-5: {hit5/n:.3f}")
json.dump(report, open(os.environ.get('OUTF', 'data/taskextractor/discovered_origins.json'), 'w'), indent=1)
for r in report[:30]:
    t = r['top_refs'][0]
    print(f"{r['name'][:34]:34s} <- {t['first_author']} {t['year']} ({t['papers']}p, pur {t['purity']}) {t['title'][:55]} {'*' if t['curated'] else ''}")
