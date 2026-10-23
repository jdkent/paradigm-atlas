"""H7: papers sharing authors (esp. senior/last author) reuse the same paradigm more than chance."""
import json, sys, glob, collections, itertools, random
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
from taskcat.authors import name_key
L = Lexicon()
meta = {}
for f in glob.glob('data/pubmed/meta_*.jsonl'):
    for l in open(f):
        r = json.loads(l); meta[r['pmid']] = r
man = {r['dbid']: r for r in map(json.loads, open('data/manifest.jsonl'))}
rows = [json.loads(l) for l in open('data/taskextractor/te_tasks.jsonl')]
lab = collections.defaultdict(set)
for r in rows:
    if r['kind'] == 'none': continue
    m = L.match(r.get('TaskName'))
    if m and m[0] != 'hedtsk_rest': lab[r['dbid']].add(m[0])
pa = {}
for d in lab:
    p = man.get(d, {}).get('pmid')
    if p in meta and meta[p]['authors']:
        ks = [name_key(a) for a in meta[p]['authors'] if name_key(a)]
        if ks: pa[d] = (set(ks), ks[-1], ks[0], meta[p].get('year'))
print('papers w/ lexical non-rest labels & authors:', len(pa))
by_any = collections.defaultdict(set); by_last = collections.defaultdict(set); by_first = collections.defaultdict(set)
for d, (ks, last, first, y) in pa.items():
    for k in ks: by_any[k].add(d)
    by_last[last].add(d); by_first[first].add(d)
def overlap(a, b): return bool(lab[a] & lab[b])
def pairs_from(index, cap=60):
    out = set()
    for k, ds in index.items():
        ds = sorted(ds)[:cap]
        if 2 <= len(ds):
            for a, b in itertools.combinations(ds, 2): out.add((a, b))
    return out
random.seed(0)
P_last = pairs_from(by_last); P_any = pairs_from(by_any) - P_last; P_first = pairs_from(by_first) - P_last
ds = list(pa)
P_rand = {tuple(sorted(random.sample(ds, 2))) for _ in range(50000)}
for name, P in [('same last(senior) author', P_last), ('same first author (not same last)', P_first),
                ('share any other author', P_any), ('random', P_rand)]:
    P = list(P)
    print(f'{name:38s} pairs={len(P):7d}  P(share a canonical task)={sum(overlap(a,b) for a,b in P)/max(1,len(P)):.3f}')
