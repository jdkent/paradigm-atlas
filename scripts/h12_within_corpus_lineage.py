"""H12: task-adjacent citations to OTHER corpus papers link same-task instances -> within-corpus lineage chains."""
import json, pickle, collections, sys
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
L = Lexicon(); fam = lambda k: (L.family.get(k) or [None])[0]
vec, clf = pickle.load(open('data/citation_role_lineage_clf.pkl', 'rb'))
man = {r['dbid']: r for r in map(json.loads, open('data/manifest.jsonl'))}
pmid2d = {r['pmid']: d for d, r in man.items() if r.get('pmid')}
doi2d = {r['doi'].lower(): d for d, r in man.items() if r.get('doi')}
N = [json.loads(l) for l in open('data/taskextractor/te_normalized.jsonl')]
plabs = collections.defaultdict(set)
for r in N:
    if r['canonical'] and r['canonical'] != 'hedtsk_rest': plabs[r['dbid']].add(r['canonical'])
lab = {r['mid']: r['canonical'] for r in N}
rows = [json.loads(l) for l in open('data/taskextractor/te_citations_ctx.jsonl')]
edges = []
for r in rows:
    a = lab.get(r['mid'])
    if not a or a == 'hedtsk_rest': continue
    for x in r['refs']:
        d = pmid2d.get(str(x.get('pmid'))) if x.get('pmid') else None
        d = d or (doi2d.get(x['doi'].lower()) if x.get('doi') else None)
        if d and d != r['dbid'] and plabs.get(d):
            p = clf.predict_proba(vec.transform([x.get('context') or '']))[0][list(clf.classes_).index('lineage')]
            edges.append((r['dbid'], a, d, plabs[d], p))
print('task-adjacent citations to other corpus papers with labels:', len(edges))
for thr in (0.0, 0.5, 0.7):
    E = [e for e in edges if e[4] >= thr]
    same = sum(e[1] in e[3] for e in E); samef = sum(fam(e[1]) in {fam(t) for t in e[3]} for e in E)
    print(f"p_lineage>={thr}: edges {len(E)}  cited paper runs same task {same/len(E):.3f}  same family {samef/len(E):.3f}")
# lineage trees: per task, in-corpus citation DAG among papers running that task
G = collections.defaultdict(lambda: collections.defaultdict(set))
for s, a, d, ts, p in edges:
    if a in ts and p >= 0.5: G[a][s].add(d)
summ = []
for t, g in G.items():
    nodes = set(g) | {d for v in g.values() for d in v}
    indeg = collections.Counter(d for v in g.values() for d in v)
    # depth: longest chain via DFS (DAG assumed; cap)
    memo = {}
    def depth(n, seen=()):
        if n in memo: return memo[n]
        if n in seen: return 0
        v = 1 + max((depth(c, seen + (n,)) for c in g.get(n, ())), default=0); memo[n] = v; return v
    D = max(depth(n) for n in g)
    hub, hk = indeg.most_common(1)[0]
    summ.append((len(nodes), D, t, hub, hk))
summ.sort(reverse=True)
print('task lineage graphs (papers, longest chain, hub paper, hub in-degree):')
for n, D, t, hub, hk in summ[:15]:
    print(f"  {L.names.get(t)[:36]:36s} papers={n:4d} depth={D:2d} hub={hub} ({(man[hub].get('title') or '')[:50]}, {man[hub].get('year')}) in={hk}")
json.dump([{"task": t, "papers": n, "depth": D, "hub": hub, "hub_in": hk} for n, D, t, hub, hk in summ],
          open('data/taskextractor/within_corpus_lineage.json', 'w'), indent=0)
json.dump([list(e[:3]) + [sorted(e[3]), e[4]] for e in edges], open('data/taskextractor/within_corpus_edges.json', 'w'))
