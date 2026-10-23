"""H6: predict a mention's canonical task from the references it cites (leave-one-paper-out purity vote).
Reference 'taskness' = how concentrated the canonical labels of OTHER papers citing it are."""
import json, collections, sys, math
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
L = Lexicon()
rows = [json.loads(l) for l in open('data/taskextractor/te_citations.jsonl')]
def rkey(x):
    if x.get('pmid'): return 'pmid:' + str(x['pmid'])
    if x.get('doi'): return 'doi:' + x['doi'].lower()
    fa = (x.get('first_author') or '').strip().lower()
    t = (x.get('title') or '')[:50].lower()
    return f'ay:{fa}:{x.get("year")}:{t}' if fa and x.get('year') and len(t) > 10 else None
lab = {}
for r in rows:
    m = L.match(r['name']); lab[(r['dbid'], r['idx'])] = m[0] if m else None
cites = collections.defaultdict(lambda: collections.defaultdict(set))  # ref -> label -> papers
mrefs = {}
for r in rows:
    ks = {rkey(x) for x in r['refs']} - {None}
    mrefs[(r['dbid'], r['idx'])] = ks
    l = lab[(r['dbid'], r['idx'])]
    for k in ks:
        cites[k][l].add(r['dbid'])
def predict(m, min_support=2):
    votes = collections.Counter(); d = m[0]
    for k in mrefs[m]:
        dist = {l: len(ps - {d}) for l, ps in cites[k].items() if l is not None}
        tot = sum(dist.values())
        if tot < min_support: continue
        l, c = max(dist.items(), key=lambda kv: kv[1])
        purity = c / tot
        if purity >= 0.5: votes[l] += purity * math.log(1 + tot)
    if not votes: return None, 0
    l, s = votes.most_common(1)[0]
    return l, s / sum(votes.values())
for excl_rest in (True,):
    ev = [m for m, l in lab.items() if l and mrefs[m] and not (excl_rest and l == 'hedtsk_rest')]
    for thr in (0.0, 0.5, 0.7, 0.9):
        n = c = 0
        for m in ev:
            p, conf = predict(m)
            if p is None or conf < thr: continue
            n += 1; c += p == lab[m]
        print(f'labeled non-rest mentions w/ refs={len(ev)} conf>={thr}: coverage={n/len(ev):.3f} acc={c/max(1,n):.3f}')
unl = [m for m, l in lab.items() if l is None and mrefs[m]]
preds = collections.Counter()
covered = 0
for m in unl:
    p, conf = predict(m)
    if p and conf >= 0.7: covered += 1; preds[p] += 1
print(f'unlabeled mentions with refs: {len(unl)}; citation route labels {covered} at conf>=0.7')
print(preds.most_common(25))
fam = lambda k: (L.family.get(k) or [None])[0]
ev = [m for m, l in lab.items() if l and mrefs[m] and l != 'hedtsk_rest']
n = c = cf = 0
for m in ev:
    p, conf = predict(m)
    if p is None or conf < 0.7: continue
    n += 1; c += p == lab[m]; cf += fam(p) == fam(lab[m])
print(f'conf>=0.7: task acc {c/n:.3f}, family acc {cf/n:.3f}')
