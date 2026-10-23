"""Self-audit: mentions citing a reference that is strongly specific to task X, but labeled Y != X."""
import json, collections, sys
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
L = Lexicon()
N = {r['mid']: r for r in map(json.loads, open('data/taskextractor/te_normalized.jsonl'))}
cit = [json.loads(l) for l in open('data/taskextractor/te_citations.jsonl')]
def rkey(x):
    if x.get('doi'): return 'doi:' + x['doi'].lower().strip()
    if x.get('pmid'): return 'pmid:' + str(x['pmid'])
    return None
by = collections.defaultdict(lambda: collections.defaultdict(set)); info = {}
for c in cit:
    lab = N.get(c['mid'], {}).get('canonical')
    for x in c['refs']:
        k = rkey(x)
        if k: by[k][lab].add(c['mid']); info[k] = x
pairs = collections.Counter(); ex = collections.defaultdict(list)
for k, d in by.items():
    tot = sum(len(v) for l, v in d.items() if l)
    for X, ms in d.items():
        if not X or len(ms) < 5 or len(ms) / tot < 0.7: continue
        for Y, ms2 in d.items():
            if Y and Y != X:
                for m in ms2:
                    pairs[(Y, X)] += 1; ex[(Y, X)].append((N[m]['name'], info[k].get('first_author'), info[k].get('year')))
print('candidate mislabels:', sum(pairs.values()))
for (Y, X), n in pairs.most_common(25):
    print(f"{n:3d}  labeled {L.names.get(Y, Y)[:30]:30s} but cites {X} ref: e.g. {ex[(Y,X)][0]}")
