"""H4b: TF-IDF route B (CPU) vs Qwen-embedding route B on masked procedure text."""
import json, sys, collections, pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.model_selection import GroupKFold
from scipy.sparse import hstack
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
L = Lexicon(); fam = lambda k: (L.family.get(k) or [None])[0]
meta = [json.loads(l) for l in open('data/taskextractor/te_proc_meta.jsonl')]
E = np.load('data/taskextractor/te_proc_emb.npy').astype(np.float32)
lab = [(L.match(m['name']) or [None])[0] for m in meta]
cnt = collections.Counter(l for l in lab if l)
keep = [i for i, l in enumerate(lab) if l and cnt[l] >= 25]
y = np.array([lab[i] for i in keep]); g = np.array([meta[i]['dbid'] for i in keep])
texts = [meta[i]['masked'] for i in keep]
vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=50000, sublinear_tf=True)
X = vec.fit_transform(texts)
for name, XX in (('tfidf', X),):
    P = np.empty(len(y), dtype=object); C = np.zeros(len(y))
    for tr, te in GroupKFold(5).split(XX, y, g):
        clf = (SGDClassifier(loss='log_loss', alpha=2e-6, max_iter=30, tol=None, random_state=0, n_jobs=8) if name == 'tfidf' else LogisticRegression(max_iter=2000, C=4.0)).fit(XX[tr], y[tr])
        pr = clf.predict_proba(XX[te]); P[te] = clf.classes_[pr.argmax(1)]; C[te] = pr.max(1)
    m = C >= 0.6
    print(f"{name}: acc {(P == y).mean():.3f} family {np.mean([fam(a) == fam(b) for a, b in zip(P, y)]):.3f} | conf>=.6 cov {m.mean():.3f} acc {(P[m] == y[m]).mean():.3f}")
clf = SGDClassifier(loss='log_loss', alpha=2e-6, max_iter=30, tol=None, random_state=0, n_jobs=8).fit(X, y)
pickle.dump((vec, clf), open('data/routeB_tfidf.pkl', 'wb')); print('saved data/routeB_tfidf.pkl')
