"""Route B v2: TF-IDF+SGD trained on TE masked procedures + A-labeled cards (neuro silver/gold + psych)."""
import json, sys, collections, pickle, glob
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import GroupKFold
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
from taskcat.cards import CardBuilder
L = Lexicon(); CB = CardBuilder()
X, y, g, src = [], [], [], []
for m in map(json.loads, open('data/taskextractor/te_proc_meta.jsonl')):
    lab = (L.match(m['name']) or [None])[0]
    if lab: X.append(m['masked']); y.append(lab); g.append(m['dbid']); src.append('te')
for f in ['data/cards/psych_v2.jsonl', 'data/cards/gold_v2.jsonl']:
    for c in map(json.loads, open(f)):
        t = c['mention']; lab = (L.match(t.get('paradigm_term')) or L.match(t.get('name')) or [None])[0]
        if lab and c['entity_kind'] not in ('questionnaire_or_scale', 'intervention_or_training'):
            X.append(CB.procedure_text(t)); y.append(lab); g.append(c['dbid']); src.append('psych' if c['dbid'].startswith('PMC') else 'cards')
cnt = collections.Counter(y); keep = [i for i, l in enumerate(y) if cnt[l] >= 15]
X = [X[i] for i in keep]; y = np.array([y[i] for i in keep]); g = np.array([g[i] for i in keep]); src = np.array([src[i] for i in keep])
print('examples', len(y), collections.Counter(src), 'classes', len(set(y)))
vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=60000, sublinear_tf=True); Xv = vec.fit_transform(X)
mk = lambda: SGDClassifier(loss='log_loss', alpha=2e-6, max_iter=30, tol=None, random_state=0, n_jobs=8)
P = np.empty(len(y), dtype=object); C = np.zeros(len(y))
for tr, te in GroupKFold(5).split(Xv, y, g):
    clf = mk().fit(Xv[tr], y[tr]); pr = clf.predict_proba(Xv[te]); P[te] = clf.classes_[pr.argmax(1)]; C[te] = pr.max(1)
for s in ('te', 'psych', 'cards'):
    m = src == s
    if m.sum(): print(f"  {s}: acc {(P[m] == y[m]).mean():.3f} | conf>=.6 cov {(C[m] >= .6).mean():.3f} acc {(P[m][C[m] >= .6] == y[m][C[m] >= .6]).mean():.3f} (n={m.sum()})")
clf = mk().fit(Xv, y); pickle.dump((vec, clf), open('data/routeB_tfidf.pkl', 'wb')); print('saved')
