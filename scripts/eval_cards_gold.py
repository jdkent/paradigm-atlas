"""Score card identities (instance_id keyed) against an annotated gold file (mid = instance_id)."""
import json, sys, collections
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
L = Lexicon(); fam = lambda k: (L.family.get(k) or [None])[0] if k else None
cards = {c['instance_id']: c for c in map(json.loads, open(sys.argv[1]))}
G = json.load(open(sys.argv[2]))
NT = {'not_a_task', 'questionnaire_or_scale', 'intervention_or_training'}
s = collections.Counter(); byroute = collections.defaultdict(collections.Counter)
for g in G:
    c = cards.get(g['mid'])
    if not c: s['missing'] += 1; continue
    p = c['identity']['canonical_task']; gc = g['canonical']
    if g['entity_kind'] in NT: s['gold_nontask'] += 1; s['nontask_given_label'] += bool(p); continue
    if gc and gc.startswith('NEW'):
        s['gold_new'] += 1; s['new_labeled'] += bool(p); continue
    if not gc: continue
    s['inv'] += 1
    if p:
        s['lab'] += 1; ok = p == gc or p == g.get('alt'); s['ok'] += ok; s['fam'] += fam(p) == fam(gc)
        r = (c['identity']['route'] or '').split(':')[0]; byroute[r]['n'] += 1; byroute[r]['ok'] += ok
print(f"inventory items {s['inv']}: coverage {s['lab']/s['inv']:.3f}, exact|alt {s['ok']/max(1,s['lab']):.3f}, family {s['fam']/max(1,s['lab']):.3f}")
print(f"gold NEW {s['gold_new']}: given an inventory label {s['new_labeled']}; gold non-task {s['gold_nontask']}: labeled {s['nontask_given_label']}")
for r, c in byroute.items(): print(f"  route {r}: n={c['n']} acc={c['ok']/c['n']:.3f}")
