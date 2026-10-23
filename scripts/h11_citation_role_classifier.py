"""H11a: citation role is predictable from the citing sentence (silver Luna roles). TF-IDF + LR, 5-fold by paper."""
import json, glob, re, collections, sys, pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import classification_report, f1_score
sys.path.insert(0, '.')
from taskcat.validate import squash
pas = {json.loads(l)['dbid']: json.loads(l)['passage'] for l in open('data/passages_train.jsonl')}
SENT = re.compile(r'(?<=[.!?])\s+(?=[A-Z(\[])')
X, y, g = [], [], []
for f in glob.glob('data/silver/train_luna/*.json'):
    j = json.load(open(f)); d = j['dbid']; P = pas.get(d)
    if not P or not j.get('parsed'): continue
    sents = [s for p in P.split('\n') for s in SENT.split(p)]
    for t in j['parsed'].get('tasks') or []:
        for c in t.get('citations') or []:
            m, role = c.get('marker'), c.get('role')
            if isinstance(role, list): role = role[0] if role else None
            if not m or not role: continue
            sm = squash(m)
            ctx = next((s for s in sents if sm and sm in squash(s)), None)
            if not ctx: continue
            ctx = ctx.replace(m, ' [CIT] ')
            X.append(ctx[:600]); y.append(role); g.append(d)
y = np.array(y); g = np.array(g)
print('examples', len(X), collections.Counter(y).most_common())
LINE = {'task_origin', 'adapted_from', 'prior_use', 'stimulus_set'}
yb = np.array(['lineage' if r in LINE else 'other' for r in y])
vec = TfidfVectorizer(ngram_range=(1, 3), min_df=2, sublinear_tf=True)
Xv = vec.fit_transform(X)
for name, Y in (('8-way', y), ('lineage-vs-other', yb)):
    P = np.empty(len(Y), dtype=object)
    for tr, te in GroupKFold(5).split(Xv, Y, g):
        clf = LogisticRegression(max_iter=3000, C=4, class_weight='balanced').fit(Xv[tr], Y[tr]); P[te] = clf.predict(Xv[te])
    print(name, 'macro-F1', round(f1_score(Y, P, average='macro'), 3), 'acc', round((P == Y).mean(), 3))
    if name != '8-way': print(classification_report(Y, P, digits=3))
clf = LogisticRegression(max_iter=3000, C=4, class_weight='balanced').fit(Xv, yb)
pickle.dump((vec, clf), open('data/citation_role_lineage_clf.pkl', 'wb'))
