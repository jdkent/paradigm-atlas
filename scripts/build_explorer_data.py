"""Aggregate per-canonical-task summaries for the explorer page -> data/explorer.json"""
import json, glob, collections, sys
import numpy as np
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
from taskcat.decompose import STEM_OF
from taskcat.authors import name_key
L = Lexicon(); fam = lambda k: (L.family.get(k) or [None])[0]
N = [json.loads(l) for l in open('data/taskextractor/te_normalized.jsonl')]
man = {r['dbid']: r for r in map(json.loads, open('data/manifest.jsonl'))}
pm = {}
for f in glob.glob('data/pubmed/meta_*.jsonl'):
    for l in open(f):
        r = json.loads(l); pm[r['pmid']] = r
year = {}; senior = {}
for d, r in man.items():
    rec = pm.get(r.get('pmid'))
    if rec:
        try: year[d] = int(str(rec.get('year'))[:4])
        except Exception: pass
        if rec['authors']:
            a = rec['authors'][-1]; senior[d] = f"{a.get('last')} {(a.get('initials') or '')}".strip()
by = collections.defaultdict(list)
for r in N:
    if r['canonical']: by[r['canonical']].append(r)
origins = {o['task']: o['top_refs'] for o in json.load(open('data/taskextractor/discovered_origins.json'))}
tasks_sim = json.load(open('data/taskextractor/task_sim_tasks.json')); S = np.load('data/taskextractor/task_sim_combined.npy')
ts = {t: i for i, t in enumerate(tasks_sim)}
kinds = collections.Counter(r['entity_kind'] for r in N)
out = {"summary": {"mentions": len(N), "papers": len({r['dbid'] for r in N}), "labeled": sum(1 for r in N if r['canonical']),
                   "entity_kinds": kinds.most_common(), "n_tasks": len(by)}, "tasks": []}
for k, rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
    papers = {r['dbid'] for r in rs}
    yrs = collections.Counter(year[d] for d in papers if d in year and 1995 <= year[d] <= 2025)
    quals = collections.Counter(f"{q['text']}|{q['axis']}" for r in rs for q in r.get('qualifiers') or [] if q['axis'] != 'other')
    names = collections.Counter(r['name'] for r in rs)
    labs = collections.Counter(senior[d] for d in papers if d in senior)
    rel = []
    if k in ts:
        i = ts[k]; order = np.argsort(-S[i])
        rel = [{"task": tasks_sim[j], "name": L.names.get(tasks_sim[j]), "sim": round(float(S[i, j]), 3)} for j in order if j != i][:6]
    out["tasks"].append({
        "id": k, "name": L.names.get(k), "family": fam(k), "stem": STEM_OF.get(k, k), "source": "hed-task" if k.startswith('hedtsk') else "corpus-extension",
        "definition": (L.tasks.get(k) or {}).get('short_definition'), "mentions": len(rs), "papers": len(papers),
        "routes": collections.Counter(r['route'] for r in rs).most_common(), "years": sorted(yrs.items()),
        "top_names": names.most_common(8), "qualifiers": quals.most_common(10), "labs": labs.most_common(8),
        "origins": origins.get(k, [])[:5], "related": rel})
json.dump(out, open('data/explorer.json', 'w'))
print(len(out['tasks']), 'tasks;', round(len(json.dumps(out)) / 1e6, 2), 'MB')

# --- enrich with extractor TaskCards: corpus split + typical facet profile
import glob as _g
prof = collections.defaultdict(lambda: {"corpus": collections.Counter(), "sk": collections.Counter(), "rk": collections.Counter(),
                                        "dt": collections.Counter(), "sm": collections.Counter(), "n": 0})
for f in ['data/cards/gold_v2.jsonl', 'data/cards/train_luna_v2.jsonl', 'data/cards/train_rest_v2.jsonl', 'data/cards/psych_v3.jsonl']:
    for l in open(f):
        c = json.loads(l); k = c['identity']['canonical_task']
        if not k: continue
        P = prof[k]; P['n'] += 1; P['corpus'][c.get('corpus')] += 1
        for s in {x['value'] for x in c['facets']['stimulus_kind']}: P['sk'][s] += 1
        for r in c['facets']['response_kind']: P['rk'][r] += 1
        for m in c['facets']['stimulus_modality']: P['sm'][m] += 1
        if c['facets']['design_type']: P['dt'][c['facets']['design_type']] += 1
E = json.load(open('data/explorer.json'))
for t in E['tasks']:
    P = prof.get(t['id'])
    t['profile'] = {"n": P['n'], "corpus": P['corpus'].most_common(), "stimuli": P['sk'].most_common(5), "modality": P['sm'].most_common(3),
                    "response": P['rk'].most_common(4), "design": P['dt'].most_common(3)} if P else None
json.dump(E, open('data/explorer.json', 'w')); print('profiles added', sum(1 for t in E['tasks'] if t.get('profile')))
