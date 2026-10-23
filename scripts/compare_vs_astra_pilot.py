"""Pilot: score Luna single runs / 2-run union / full protocol / old silver against single-run astra (v0.4)."""
import json, glob, sys, collections, statistics, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.evaluate import evaluate
from taskcat import sentence_schema as S, consensus as K
pas = {json.loads(l)["dbid"]: json.loads(l) for l in open("data/passages_pilot50.jsonl")}
passages = {d: r["passage"] for d, r in pas.items()}
A, G, U = {}, collections.Counter(), []
for f in glob.glob("data/silver/pilot50_astra/*.json"):
    j = json.load(open(f)); A[j["dbid"]] = j["parsed"]; G.update(j["grounding"]); U.append(j["usage"])
print(f"astra: papers {len(A)} | grounding {dict(G)} rate {G['grounded']/G['labels']:.3f}")
print("astra per call: in %.0f out %.0f reasoning %.0f | tasks/paper %.2f" % (
    statistics.mean(u["prompt_tokens"] for u in U), statistics.mean(u["completion_tokens"] for u in U),
    statistics.mean((u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) for u in U),
    sum(len(a["tasks"]) for a in A.values()) / len(A)))
runs = {k: {json.load(open(f))["dbid"]: json.load(open(f))["parsed_s"] for f in glob.glob(f"data/silver/pilot50_luna6/run{k}/*.json")} for k in (1, 2, 3)}
conv = lambda d, x: S.to_mention(x, passages[d])[0]
R = {"luna run1": {d: conv(d, x) for d, x in runs[1].items() if x},
     "luna run2": {d: conv(d, x) for d, x in runs[2].items() if x},
     "luna 2-run union": {d: conv(d, K.merge([runs[1][d], runs[2][d]])[0]) for d in runs[1] if d in runs[2]},
     "luna full protocol": {json.load(open(f))["dbid"]: json.load(open(f))["parsed"] for f in glob.glob("data/silver/pilot50_luna6/consensus/*.json")}}
old = {}
for od in ["data/silver/train_luna", "data/silver/psych_luna"]:
    for f in glob.glob(od + "/*.json"):
        j = json.load(open(f))
        if j.get("parsed") and j["dbid"] in A: old[j["dbid"]] = j["parsed"]
R["old gpt-5.6 silver"] = old
keys = ["task_P", "task_R", "task_F1", "entity_kind", "design_type", "conditions", "stim_content", "citations",
        "cit_role", "judgment", "resp_kind", "measures"]
print("=== vs astra (reference)")
for name, P in R.items():
    sub = {d: P[d] for d in A if d in P}
    e = evaluate(sub, {d: A[d] for d in sub}, passages)
    print(f"{name:20s} n={len(sub):2d} " + " ".join(f"{k}={e.get(k, float('nan')):.2f}" for k in keys))
