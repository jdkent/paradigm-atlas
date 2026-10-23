"""Cluster unlabeled residue mentions into candidate new canonical tasks (two channels: name, masked procedure)."""
import json, re, collections, sys
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
R = [json.loads(l) for l in open('data/taskextractor/te_normalized.jsonl')]
meta = [json.loads(l) for l in open('data/taskextractor/te_proc_meta.jsonl')]
P = np.load('data/taskextractor/te_proc_emb.npy').astype(np.float32)
pos = {(m['dbid'], m['idx']): i for i, m in enumerate(meta)}
res = [r for r in R if r['canonical'] is None and r['route'] != 'gate']
def nn(s): return re.sub(r'\s*\([^)]*\)', '', (s or '')).strip()
names = [nn(r['name']) for r in res]
M = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
N = M.encode(names, batch_size=256, normalize_embeddings=True, show_progress_bar=False)
Pr = P[[pos[(r['dbid'], r['idx'])] for r in res]]
S = 0.55 * (N @ N.T) + 0.45 * (Pr @ Pr.T)
D = np.clip(1 - S, 0, 2).astype(np.float32); del S
cl = AgglomerativeClustering(n_clusters=None, metric='precomputed', linkage='average', distance_threshold=0.42).fit(D)
lab = cl.labels_
groups = collections.defaultdict(list)
for r, l, n in zip(res, lab, names): groups[l].append((r, n))
cands = []
for l, g in groups.items():
    papers = {r['dbid'] for r, _ in g}
    if len(papers) < 4: continue
    nc = collections.Counter(n.lower() for _, n in g)
    cands.append({"cluster": int(l), "n_mentions": len(g), "n_papers": len(papers), "label": nc.most_common(1)[0][0],
                  "names": nc.most_common(8), "members": [f"{r['dbid']}#{r['idx']}" for r, _ in g]})
cands.sort(key=lambda c: -c['n_papers'])
json.dump(cands, open('data/taskextractor/residue_clusters.json', 'w'), indent=0)
print('residue', len(res), 'clusters', len(groups), 'clusters with >=4 papers', len(cands),
      'mentions covered', sum(c['n_mentions'] for c in cands))
for c in cands[:70]: print(c['n_papers'], '|', c['label'], '|', [n for n, _ in c['names'][1:5]])
