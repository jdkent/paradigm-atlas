"""Consensus silver labels: gpt-6-luna x2 (strict sentence-indexed schema, Flex, reasoning medium); a 3rd run only
when the two runs disagree in a consumption-relevant way (taskcat.consensus.needs_third); then merge + convert.
Usage: silver_consensus.py PASSAGES OUTDIR [N] [PAPER_WORKERS]   env MAX_IN / MAX_OUT (hard cap for this OUTDIR)
Layout: OUTDIR/run{1,2,3}/<dbid>.json, OUTDIR/consensus/<dbid>.json"""
import json, os, sys, glob, threading
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.llm import load_env, chat, parse_json, DEFAULT_MODEL
from taskcat import sentence_schema as S, consensus as K
load_env()
inp, out = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9; W = int(sys.argv[4]) if len(sys.argv) > 4 else 6
MAX_IN, MAX_OUT = int(os.environ.get("MAX_IN", 0)), int(os.environ.get("MAX_OUT", 0))
for d in ("run1", "run2", "run3", "consensus"): os.makedirs(os.path.join(out, d), exist_ok=True)
lock = threading.Lock(); used = {"in": 0, "out": 0}
for f in glob.glob(os.path.join(out, "run*", "*.json")):
    u = (json.load(open(f)).get("usage") or {}); used["in"] += u.get("prompt_tokens", 0) or 0; used["out"] += u.get("completion_tokens", 0) or 0
def over(): return (MAX_IN and used["in"] >= MAX_IN) or (MAX_OUT and used["out"] >= MAX_OUT)
def run(r, k):
    p = os.path.join(out, f"run{k}", r["dbid"] + ".json")
    if os.path.exists(p):
        j = json.load(open(p))
        if j.get("parsed_s"): return j                 # unparsed (e.g. reasoning used the whole budget) -> redo
    if over(): return None
    content, usage = chat(S.messages(r["title"] or "", r["passage"]), DEFAULT_MODEL, schema=S.SCHEMA, schema_name="task_mentions_s",
                          reasoning_effort="medium", service_tier="flex")
    j = {"dbid": r["dbid"], "model": DEFAULT_MODEL, "run": k, "parsed_s": parse_json(content), "usage": usage}
    json.dump(j, open(p, "w"))
    with lock: used["in"] += usage.get("prompt_tokens", 0) or 0; used["out"] += usage.get("completion_tokens", 0) or 0
    return j
def paper(r):
    cp = os.path.join(out, "consensus", r["dbid"] + ".json")
    if os.path.exists(cp): return
    try:
        with ThreadPoolExecutor(2) as ex: a, b = ex.map(lambda k: run(r, k), (1, 2))
        if not a or not b: return
        third, reasons = K.needs_third(a["parsed_s"], b["parsed_s"])
        runs = [a["parsed_s"], b["parsed_s"]]
        if third:
            c = run(r, 3)
            if not c: return
            runs.append(c["parsed_s"])
        merged, rep = K.merge(runs)
        mention, stat = S.to_mention(merged, r["passage"])
        json.dump({"dbid": r["dbid"], "n_runs": len(runs), "third_reasons": reasons, "merge_report": rep,
                   "parsed_s": merged, "parsed": mention, "grounding": stat}, open(cp, "w"))
    except Exception as e:
        json.dump({"dbid": r["dbid"], "error": repr(e)[:800]}, open(cp + ".err", "w"))
rows = [json.loads(l) for l in open(inp)][:N]
with ThreadPoolExecutor(W) as ex: list(ex.map(paper, rows))
print("tokens used in this OUTDIR:", used)
