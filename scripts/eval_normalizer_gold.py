"""Score te_normalized.jsonl against the 300-mention gold (data/gold_norm/gold_{0,1}.json)."""
import json, collections, sys
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon
L = Lexicon(); fam = lambda k: (L.family.get(k) or [None])[0] if k else None
import os
G = [g for f in os.environ.get('GOLD', 'data/gold_norm/gold_0.json,data/gold_norm/gold_1.json').split(',') for g in json.load(open(f))]
N = {r['mid']: r for r in map(json.loads, open(sys.argv[1] if len(sys.argv) > 1 else 'data/taskextractor/te_normalized.jsonl'))}
NONTASK = {'not_a_task', 'questionnaire_or_scale', 'intervention_or_training'}
s = collections.Counter(); per_route = collections.defaultdict(collections.Counter)
for g in G:
    n = N[g['mid']]
    gold_nt = g['entity_kind'] in NONTASK; pred_nt = n['entity_kind'] in NONTASK
    s['gate_correct'] += gold_nt == pred_nt; s['gold_nontask'] += gold_nt; s['pred_nontask'] += pred_nt
    s['gate_tp'] += gold_nt and pred_nt
    c = g['canonical']
    EQ = {'tct_card_guessing': 'tct_reward_feedback', 'tct_stimulus_rating': 'tct_valence_judgment', 'tct_bm_bladder_control': 'tct_sensory_stimulation'}
    if n['canonical'] in EQ and c == EQ[n['canonical']]: n = {**n, 'canonical': c}
    if c and not c.startswith('NEW:'):
        s['gold_inv'] += 1
        p = n['canonical']
        if p:
            s['pred_on_inv'] += 1
            ok = p == c; okalt = ok or p == g.get('alt'); okf = fam(p) == fam(c)
            s['exact'] += ok; s['exact_or_alt'] += okalt; s['family'] += okf
            pr = per_route[n['route']]; pr['n'] += 1; pr['exact_or_alt'] += okalt; pr['family'] += okf
            if len(n['agree']) >= 2: s['agree2_n'] += 1; s['agree2_ok'] += okalt
    elif c and c.startswith('NEW:'):
        s['gold_new'] += 1; s['new_labeled'] += bool(n['canonical'])
        s['new_labeled_famok'] += bool(n['canonical'])  # placeholder
print(f"gate: acc {s['gate_correct']/len(G):.3f}  P {s['gate_tp']/max(1,s['pred_nontask']):.3f}  R {s['gate_tp']/max(1,s['gold_nontask']):.3f}")
print(f"inventory-gold items {s['gold_inv']}: coverage {s['pred_on_inv']/s['gold_inv']:.3f}; of labeled: exact {s['exact']/s['pred_on_inv']:.3f}, "
      f"exact-or-alt {s['exact_or_alt']/s['pred_on_inv']:.3f}, family {s['family']/s['pred_on_inv']:.3f}")
print(f"  >=2 routes agree: n={s['agree2_n']} acc(exact|alt)={s['agree2_ok']/max(1,s['agree2_n']):.3f}")
for r, c in per_route.items(): print(f"  route {r}: n={c['n']} exact|alt={c['exact_or_alt']/c['n']:.3f} family={c['family']/c['n']:.3f}")
print(f"gold NEW items {s['gold_new']}: wrongly given an inventory label {s['new_labeled']} ({s['new_labeled']/max(1,s['gold_new']):.2f})")
