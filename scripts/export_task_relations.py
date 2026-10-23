"""Typed task-task relation graph -> schema/task_relations.json (edges with evidence counts)."""
import json, collections, itertools, sys, glob
import numpy as np
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
from taskcat.decompose import STEM_OF
from taskcat.authors import name_key
L = Lexicon(); fam = lambda k: (L.family.get(k) or [None])[0]
edges = collections.defaultdict(lambda: collections.Counter())   # (a,b) -> {relation: weight}
def add(a, b, rel, w=1):
    if a and b and a != b: edges[tuple(sorted((a, b)))][rel] += w
ids = list(L.names)
for a, b in itertools.combinations(ids, 2):
    if STEM_OF.get(a, a) == STEM_OF.get(b, b): add(a, b, 'same_stem')
    elif fam(a) and fam(a) == fam(b): add(a, b, 'same_family')
# cards: shared origin/prior-use refs and shared stimulus sets across tasks
cards = [json.loads(l) for f in glob.glob('data/cards/*_v2.jsonl') for l in open(f)]
by = {k: collections.defaultdict(set) for k in ('origin', 'prior', 'stim')}
for c in cards:
    t = c['identity']['canonical_task']
    if not t: continue
    for p in c['lineage']['origin_refs']: by['origin'][p].add(t)
    for p in c['lineage']['prior_use_refs']: by['prior'][p].add(t)
    for s in c['facets']['stimulus_sets']: by['stim'][s.lower()[:40]].add(t)
for rel, key in (('co_cited_origin', 'origin'), ('co_cited_prior_use', 'prior'), ('shared_stimulus_set', 'stim')):
    for ref, ts in by[key].items():
        for a, b in itertools.combinations(sorted(ts), 2): add(a, b, rel)
# same lab: senior author (TE corpus labels + PubMed)
pm = {}
for f in glob.glob('data/pubmed*/meta_*.jsonl'):
    for l in open(f):
        r = json.loads(l); pm[r['pmid']] = r
man = {r['dbid']: r for r in map(json.loads, open('data/manifest.jsonl'))}
lab_tasks = collections.defaultdict(set)
for r in map(json.loads, open('data/taskextractor/te_normalized.jsonl')):
    if r['canonical'] and r['canonical'] != 'hedtsk_rest':
        rec = pm.get(man.get(r['dbid'], {}).get('pmid'))
        if rec and rec['authors']:
            a = rec['authors'][-1]
            k = (a.get('last') or '').lower() + '_' + (a.get('fore') or '').lower().replace(' ', '').replace('.', '')
            lab_tasks[k].add(r['canonical'])
lab_pairs = collections.Counter()
for k, ts in lab_tasks.items():
    if 2 <= len(ts) <= 12:
        for a, b in itertools.combinations(sorted(ts), 2): lab_pairs[(a, b)] += 1
# normalize same_lab by expectation (tasks' lab counts) -> keep pairs with lift >= 3 and >= 3 labs
labs_per = collections.Counter(t for ts in lab_tasks.values() if 2 <= len(ts) <= 12 for t in ts)
nl = sum(1 for ts in lab_tasks.values() if 2 <= len(ts) <= 12)
for (a, b), n in lab_pairs.items():
    exp = labs_per[a] * labs_per[b] / max(1, nl)
    if n >= 3 and n / max(exp, 1e-9) >= 3: add(a, b, 'same_lab', n)
# procedural similarity (TE combined matrix)
tasks = json.load(open('data/taskextractor/task_sim_tasks.json')); S = np.load('data/taskextractor/task_sim_combined.npy')
for i, t in enumerate(tasks):
    for j in np.argsort(-S[i])[1:4]:
        if np.isfinite(S[i, j]): add(t, tasks[j], 'procedural_similarity_top3', round(float(S[i, j]), 3))
out = [{"a": a, "b": b, "a_name": L.names.get(a), "b_name": L.names.get(b), "relations": dict(r)} for (a, b), r in edges.items()]
rc = collections.Counter(k for e in out for k in e['relations'])
json.dump({"n_tasks": len(ids), "relation_counts": rc, "edges": out}, open('schema/task_relations.json', 'w'), indent=0)
print(len(out), 'edges', dict(rc))
multi = sorted([e for e in out if len(set(e['relations']) - {'same_family', 'same_stem'}) >= 2], key=lambda e: -sum(v for k, v in e['relations'].items() if k not in ('same_family', 'same_stem', 'procedural_similarity_top3')))[:20]
for e in multi: print(f"  {e['a_name'][:30]:30s} ~ {e['b_name'][:30]:30s} {e['relations']}")
