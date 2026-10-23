"""Pilot report for consensus silver labels. Usage: analyze_pilot.py PASSAGES PILOT_DIR OLD_SILVER_DIRS(comma)"""
import json, os, sys, glob, collections, statistics
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.evaluate import evaluate
from taskcat import sentence_schema as S
pas = {json.loads(l)["dbid"]: json.loads(l) for l in open(sys.argv[1])}
D = sys.argv[2]; old_dirs = sys.argv[3].split(",")
cons = {json.load(open(f))["dbid"]: json.load(open(f)) for f in glob.glob(f"{D}/consensus/*.json")}
runs = {k: {json.load(open(f))["dbid"]: json.load(open(f)) for f in glob.glob(f"{D}/run{k}/*.json")} for k in (1, 2, 3)}
print(f"papers with consensus: {len(cons)}  errors: {len(glob.glob(f'{D}/consensus/*.err'))}")
n3 = sum(c["n_runs"] == 3 for c in cons.values())
print(f"third run needed: {n3}/{len(cons)} = {n3/max(1,len(cons)):.2f}")
R = collections.Counter(r.split(":")[0] for c in cons.values() for r in c["third_reasons"])
print("third-run reasons (counts over papers' reasons):", R.most_common())
U = [x["usage"] for k in runs for x in runs[k].values()]
pin = [u["prompt_tokens"] for u in U]; pout = [u["completion_tokens"] for u in U]
rsn = [(u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) for u in U]
print(f"calls {len(U)}: mean in {statistics.mean(pin):.0f}, mean out {statistics.mean(pout):.0f} (reasoning {statistics.mean(rsn):.0f}); "
      f"total in {sum(pin)}, out {sum(pout)}; per paper in {sum(pin)/max(1,len(cons)):.0f} out {sum(pout)/max(1,len(cons)):.0f}")
G = collections.Counter()
for c in cons.values(): G.update(c["grounding"])
print("consensus grounding:", dict(G), f"rate {G['grounded']/max(1,G['labels']):.3f}")
# stability: run1 vs run2 (converted mentions), and consensus vs old gpt-5.6 silver
def conv(x, d): return S.to_mention(x["parsed_s"], pas[d]["passage"])[0]
common = [d for d in runs[1] if d in runs[2] and d in pas]
P1 = {d: conv(runs[1][d], d) for d in common}; P2 = {d: conv(runs[2][d], d) for d in common}
passages = {d: pas[d]["passage"] for d in pas}
print("run1 vs run2 (stability):", json.dumps(evaluate(P1, P2, passages)))
old = {}
for od in old_dirs:
    for f in glob.glob(os.path.join(od, "*.json")):
        j = json.load(open(f))
        if j.get("parsed") and j["dbid"] in cons: old[j["dbid"]] = j["parsed"]
C = {d: c["parsed"] for d, c in cons.items() if d in old}
print(f"consensus vs old gpt-5.6-luna silver ({len(C)} papers; old as reference):", json.dumps(evaluate(C, old, passages)))
nt_new = sum(len(c["parsed"]["tasks"]) for d, c in cons.items() if d in old); nt_old = sum(len(old[d].get("tasks") or []) for d in C)
print(f"tasks per paper: consensus {nt_new/max(1,len(C)):.2f} vs old {nt_old/max(1,len(C)):.2f}")
roles = [len(c2["roles"]) for c in cons.values() for t in c["parsed_s"]["tasks"] for c2 in t["citations"]]
print(f"citations {len(roles)}: multi-role {sum(r > 1 for r in roles)} ({sum(r > 1 for r in roles)/max(1,len(roles)):.1%}), "
      f"empty-role (category tie) {sum(r == 0 for r in roles)}")
