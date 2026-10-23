"""Run the combined normalizer over the TaskExtractor corpus -> data/taskextractor/te_normalized.jsonl"""
import json, sys, glob, collections, math
import numpy as np
from sklearn.linear_model import LogisticRegression
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
from taskcat.normalize import gate, combine
from taskcat.authors import name_key
from taskcat.decompose import Decomposer, STEM_OF
L = Lexicon(); fam = lambda k: (L.family.get(k) or [None])[0]
DEC = Decomposer(L)
rows = [json.loads(l) for l in open('data/taskextractor/te_tasks.jsonl')]
rows = {r['mid']: r for r in rows if r['kind'] != 'none'}
meta = [json.loads(l) for l in open('data/taskextractor/te_proc_meta.jsonl')]
E = np.load('data/taskextractor/te_proc_emb.npy').astype(np.float32)
keys = [m['mid'] for m in meta]
paper = lambda k: k.split('#')[0]
A = {k: (L.match(rows[k].get('TaskName')) or [None])[0] for k in keys}
kind = {k: gate(rows[k].get('TaskName'), rows[k].get('RestingState'), A[k]) for k in keys}
# Route B: train on A-labeled experimental mentions
cnt = collections.Counter(A[k] for k in keys if A[k])
tr = [i for i, k in enumerate(keys) if A[k] and cnt[A[k]] >= 25 and kind[k] in ('experimental_task', 'resting_state')]
clf = LogisticRegression(max_iter=2000, C=4.0).fit(E[tr], [A[keys[i]] for i in tr])
pr = clf.predict_proba(E); top = np.argsort(-pr, 1)[:, :3]
B = {k: (clf.classes_[top[i, 0]], float(pr[i, top[i, 0]]), [clf.classes_[j] for j in top[i]]) for i, k in enumerate(keys)}
# Route C: citations
cit = {r['mid']: r for r in map(json.loads, open('data/taskextractor/te_citations.jsonl'))}
def rkey(x):
    if x.get('pmid'): return 'pmid:' + str(x['pmid'])
    if x.get('doi'): return 'doi:' + x['doi'].lower()
    fa = (x.get('first_author') or '').strip().lower(); t = (x.get('title') or '')[:50].lower()
    return f'ay:{fa}:{x.get("year")}:{t}' if fa and x.get('year') and len(t) > 10 else None
mrefs = {k: ({rkey(x) for x in cit[k]['refs']} - {None}) if k in cit else set() for k in keys}
cites = collections.defaultdict(lambda: collections.defaultdict(set))
for k in keys:
    if A[k]:
        for rk in mrefs[k]: cites[rk][A[k]].add(paper(k))
def predC(k):
    votes = collections.Counter()
    for rk in mrefs[k]:
        dist = {l: len(ps - {paper(k)}) for l, ps in cites[rk].items()}
        tot = sum(dist.values())
        if tot < 2: continue
        l, c = max(dist.items(), key=lambda kv: kv[1]); p = c / tot
        if p >= 0.5: votes[l] += p * math.log(1 + tot)
    if not votes: return None
    l, s = votes.most_common(1)[0]; return (l, s / sum(votes.values()))
C = {k: predC(k) for k in keys}
# Route D: senior author's most common task in OTHER papers
pm = {}
for f in glob.glob('data/pubmed/meta_*.jsonl'):
    for l in open(f):
        r = json.loads(l); pm[r['pmid']] = r
man = {r['dbid']: r for r in map(json.loads, open('data/manifest.jsonl'))}
last = {}
for d in {paper(k) for k in keys}:
    rec = pm.get(man.get(d, {}).get('pmid'))
    if rec and rec['authors']:
        last[d] = name_key(rec['authors'][-1])
by_last = collections.defaultdict(collections.Counter)
for k in keys:
    if A[k] and A[k] != 'hedtsk_rest' and paper(k) in last: by_last[last[paper(k)]][A[k]] += 1
def predD(k):
    a = last.get(paper(k))
    if not a: return None
    c = by_last[a].copy()
    for kk in keys_by_paper[paper(k)]:
        if A[kk] and A[kk] != 'hedtsk_rest': c[A[kk]] -= 1
    c = +c
    return c.most_common(1)[0][0] if c and c.most_common(1)[0][1] >= 2 else None
keys_by_paper = collections.defaultdict(list)
for k in keys: keys_by_paper[paper(k)].append(k)
out = open(__import__('os').environ.get('OUT', 'data/taskextractor/te_normalized.jsonl'), 'w'); stats = collections.Counter()
for k in keys:
    D = predD(k)
    if kind[k] in ('not_a_task', 'questionnaire_or_scale', 'intervention_or_training'):
        lab, route, agree = None, 'gate', []
    else:
        lab, route, agree = combine(A[k], B[k], C[k], D, fam, TB=float(__import__("os").environ.get("TB", 0.6)))
    stats[kind[k]] += 1; stats['route_' + str(route)] += 1; stats['n_agree_' + str(len(agree))] += 1
    dec = DEC(rows[k].get('TaskName')) if lab else {"qualifiers": [], "variant": None}
    if lab and dec.get("canonical_task") == "hedtsk_emotional_stroop" and lab == "hedtsk_stroop_color_word": lab = "hedtsk_emotional_stroop"
    out.write(json.dumps({"stem": STEM_OF.get(lab, lab) if lab else None, "variant": dec.get("variant") if dec.get("canonical_task") == lab else None,
                          "qualifiers": dec["qualifiers"], "mid": k, "dbid": paper(k), "name": rows[k].get('TaskName'), "entity_kind": kind[k],
                          "canonical": lab, "family": fam(lab) if lab else None, "route": route, "agree": agree,
                          "A": A[k], "B": B[k][:2], "C": C[k], "D": D}) + "\n")
print(dict(stats))
