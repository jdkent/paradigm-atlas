"""H9: data-driven task-task similarity (procedure, co-citation, shared senior authors) recovers expert families."""
import json, collections, sys, glob
import numpy as np
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
from taskcat.authors import name_key
L = Lexicon(); fam = lambda k: (L.family.get(k) or [None])[0]
N = [json.loads(l) for l in open('data/taskextractor/te_normalized.jsonl')]
meta = [json.loads(l) for l in open('data/taskextractor/te_proc_meta.jsonl')]
E = np.load('data/taskextractor/te_proc_emb.npy').astype(np.float32)
pos = {m['mid']: i for i, m in enumerate(meta)}
lab = {r['mid']: r['canonical'] for r in N if r['canonical'] and r['canonical'] != 'hedtsk_rest'}
cnt = collections.Counter(lab.values())
tasks = sorted(t for t, c in cnt.items() if c >= 15 and fam(t) and fam(t) != 'pseudo_tasks')
ti = {t: i for i, t in enumerate(tasks)}
# procedure centroids
P = np.zeros((len(tasks), E.shape[1]), np.float32)
for m, t in lab.items():
    if t in ti: P[ti[t]] += E[pos[m]]
P /= np.linalg.norm(P, axis=1, keepdims=True)
# co-citation vectors (tf-idf over refs)
cit = {r['mid']: r for r in map(json.loads, open('data/taskextractor/te_citations.jsonl'))}
refs = collections.defaultdict(collections.Counter)
for m, t in lab.items():
    if t in ti and m in cit:
        for x in cit[m]['refs']:
            k = x.get('doi') or x.get('pmid')
            if k: refs[t][k] += 1
vocab = {k: i for i, k in enumerate({k for c in refs.values() for k in c})}
Cm = np.zeros((len(tasks), len(vocab)), np.float32)
for t, c in refs.items():
    for k, v in c.items(): Cm[ti[t], vocab[k]] = v
df = (Cm > 0).sum(0); Cm = Cm * np.log(len(tasks) / np.maximum(df, 1))
Cm /= np.maximum(np.linalg.norm(Cm, axis=1, keepdims=True), 1e-9)
# senior-author vectors
pm = {}
for f in glob.glob('data/pubmed/meta_*.jsonl'):
    for l in open(f):
        r = json.loads(l); pm[r['pmid']] = r
man = {r['dbid']: r for r in map(json.loads, open('data/manifest.jsonl'))}
au = collections.defaultdict(collections.Counter)
for m, t in lab.items():
    if t not in ti: continue
    rec = pm.get(man.get(m.split('#')[0], {}).get('pmid'))
    if rec and rec['authors']: au[t][name_key(rec['authors'][-1])] += 1
av = {k: i for i, k in enumerate({k for c in au.values() for k in c})}
Am = np.zeros((len(tasks), len(av)), np.float32)
for t, c in au.items():
    for k, v in c.items(): Am[ti[t], av[k]] = v
df = (Am > 0).sum(0); Am = Am * np.log(len(tasks) / np.maximum(df, 1))
Am /= np.maximum(np.linalg.norm(Am, axis=1, keepdims=True), 1e-9)
F = np.array([fam(t) for t in tasks])
from sklearn.metrics import adjusted_rand_score
from sklearn.cluster import AgglomerativeClustering
rng = np.random.default_rng(0)
def evaluate(name, S):
    S = S.copy(); np.fill_diagonal(S, -np.inf)
    nn = S.argmax(1); acc = (F[nn] == F).mean()
    base = np.mean([(F[rng.permutation(len(F))] == F).mean() for _ in range(200)])
    D = 1 - np.where(np.isfinite(S), S, 1)
    k = len(set(F))
    cl = AgglomerativeClustering(n_clusters=k, metric='precomputed', linkage='average').fit(np.clip(D, 0, 2))
    print(f"{name:18s} nearest-neighbour same-family {acc:.3f} (chance {base:.3f}); ARI vs hed families {adjusted_rand_score(F, cl.labels_):.3f}")
    return S
print('tasks', len(tasks), 'families', len(set(F)))
Sp = evaluate('procedure', P @ P.T); Sc = evaluate('co-citation', Cm @ Cm.T); Sa = evaluate('senior-author', Am @ Am.T)
Scomb = evaluate('combined', (P @ P.T) * 0.5 + (Cm @ Cm.T) * 0.3 + (Am @ Am.T) * 0.2)
np.save('data/taskextractor/task_sim_combined.npy', Scomb); json.dump(tasks, open('data/taskextractor/task_sim_tasks.json', 'w'))
# most related cross-family pairs under combined (interesting relations)
S = Scomb.copy(); iu = np.triu_indices(len(tasks), 1)
order = np.argsort(-S[iu])
print('top related pairs (cross-family marked *):')
shown = 0
for o in order[:400]:
    i, j = iu[0][o], iu[1][o]
    if F[i] != F[j]:
        print(f"  * {L.names[tasks[i]][:32]:32s} ~ {L.names[tasks[j]][:32]:32s} {S[i,j]:.2f}  ({F[i]} / {F[j]})"); shown += 1
    if shown >= 15: break
