"""H4: masked procedure text (no task name / paradigm terms) predicts the lexical canonical task.
Logistic regression on Qwen3-Embedding-0.6B vectors; GroupKFold by paper; classes with >= 25 mentions."""
import json, sys, collections
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
L = Lexicon()
E = np.load('data/taskextractor/te_proc_emb.npy').astype(np.float32)
meta = [json.loads(l) for l in open('data/taskextractor/te_proc_meta.jsonl')]
lab = []
for m in meta:
    x = L.match(m['name']); lab.append(x[0] if x else None)
cnt = collections.Counter(l for l in lab if l)
keep = [i for i, l in enumerate(lab) if l and cnt[l] >= 25]
X = E[keep]; y = np.array([lab[i] for i in keep]); g = np.array([meta[i]['dbid'] for i in keep])
print('train mentions', len(keep), 'classes', len(set(y)))
fam = lambda k: (L.family.get(k) or [None])[0]
P = np.empty(len(y), dtype=object); C = np.zeros(len(y))
for tr, te in GroupKFold(5).split(X, y, g):
    clf = LogisticRegression(max_iter=2000, C=4.0, n_jobs=8).fit(X[tr], y[tr])
    pr = clf.predict_proba(X[te]); P[te] = clf.classes_[pr.argmax(1)]; C[te] = pr.max(1)
acc = (P == y).mean(); facc = np.mean([fam(a) == fam(b) for a, b in zip(P, y)])
print(f'5-fold grouped: task acc {acc:.3f}, family acc {facc:.3f}; majority baseline {cnt.most_common(1)[0][1]/len(y):.3f}')
for t in (0.5, 0.7, 0.9):
    m = C >= t
    print(f'  conf>={t}: coverage {m.mean():.3f}, acc {(P[m] == y[m]).mean():.3f}')
# confusion highlights
conf = collections.Counter((a, b) for a, b in zip(y, P) if a != b)
print('top confusions:', [(L.names[a], L.names[b], n) for (a, b), n in conf.most_common(12)])
# fit on all, predict unlabeled
clf = LogisticRegression(max_iter=2000, C=4.0, n_jobs=8).fit(X, y)
unl = [i for i, l in enumerate(lab) if l is None]
pr = clf.predict_proba(E[unl]); pc = clf.classes_[pr.argmax(1)]; pm = pr.max(1)
out = [{"dbid": meta[i]['dbid'], "idx": meta[i]['idx'], "name": meta[i]['name'], "pred": p, "conf": float(c)}
       for i, p, c in zip(unl, pc, pm)]
json.dump(out, open('data/taskextractor/routeB_unlabeled_preds.json', 'w'))
print('unlabeled', len(unl), 'conf>=0.7:', sum(o['conf'] >= 0.7 for o in out))
import random; random.seed(1)
for o in random.sample([o for o in out if o['conf'] >= 0.7], 15): print(f"  {o['conf']:.2f} {o['name']!r} -> {L.names[o['pred']]}")
