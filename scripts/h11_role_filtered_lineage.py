"""H11b: filtering task-adjacent citations to predicted lineage roles raises citation-route precision (H5/H6)."""
import json, pickle, collections, itertools, random, math, sys
sys.path.insert(0, '.')
vec, clf = pickle.load(open('data/citation_role_lineage_clf.pkl', 'rb'))
N = {r['mid']: r for r in map(json.loads, open('data/taskextractor/te_normalized.jsonl'))}
rows = [json.loads(l) for l in open('data/taskextractor/te_citations_ctx.jsonl')]
ctx = [x.get('context') or '' for r in rows for x in r['refs']]
pr = clf.predict_proba(vec.transform(ctx))[:, list(clf.classes_).index('lineage')]
i = 0
for r in rows:
    for x in r['refs']: x['p_lineage'] = float(pr[i]); i += 1
def rkey(x):
    if x.get('doi'): return 'doi:' + x['doi'].lower().strip()
    if x.get('pmid'): return 'pmid:' + str(x['pmid'])
    fa = (x.get('first_author') or '').strip().lower(); t = (x.get('title') or '')[:50].lower()
    return f'ay:{fa}:{x.get("year")}:{t}' if fa and x.get('year') and len(t) > 10 else None
lab = {r['mid']: (N.get(r['mid']) or {}).get('canonical') for r in rows}
def run(thr):
    mrefs = {r['mid']: {rkey(x) for x in r['refs'] if x['p_lineage'] >= thr} - {None} for r in rows}
    cites = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in rows:
        if lab[r['mid']]:
            for k in mrefs[r['mid']]: cites[k][lab[r['mid']]].add(r['dbid'])
    # H5 pairs
    key2 = collections.defaultdict(set)
    for r in rows:
        for k in mrefs[r['mid']]: key2[k].add(r['mid'])
    agree = tot = 0
    for k, ms in key2.items():
        ms = [m for m in ms if lab[m] and lab[m] != 'hedtsk_rest'][:40]
        for a, b in itertools.combinations(ms, 2):
            if a.split('#')[0] == b.split('#')[0]: continue
            tot += 1; agree += lab[a] == lab[b]
    # H6 prediction
    n = c = 0; ev = [r['mid'] for r in rows if lab[r['mid']] and lab[r['mid']] != 'hedtsk_rest' and mrefs[r['mid']]]
    for m in ev:
        votes = collections.Counter(); d = m.split('#')[0]
        for k in mrefs[m]:
            dist = {l: len(ps - {d}) for l, ps in cites[k].items()}; t = sum(dist.values())
            if t < 2: continue
            l, cc = max(dist.items(), key=lambda kv: kv[1]); p = cc / t
            if p >= 0.5: votes[l] += p * math.log(1 + t)
        if not votes: continue
        l, s = votes.most_common(1)[0]
        if s / sum(votes.values()) < 0.7: continue
        n += 1; c += l == lab[m]
    print(f"p_lineage>={thr:.1f}: H5 pairs {tot:6d} same-task {agree/max(1,tot):.3f} | H6 coverage {n/max(1,len(ev)):.3f} (of {len(ev)}) acc {c/max(1,n):.3f}")
for thr in (0.0, 0.4, 0.5, 0.6, 0.7):
    run(thr)
