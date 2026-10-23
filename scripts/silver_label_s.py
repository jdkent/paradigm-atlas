"""Silver labels with the sentence-indexed schema (v0.4) + strict structured output.
Usage: silver_label_s.py PASSAGES MODEL OUTDIR [N] [WORKERS]  (env MAX_IN/MAX_OUT budget guard, REASONING=low|medium|high)
Writes raw sentence-indexed output ('parsed_s'), the converted v0.2 TaskMention ('parsed') and a grounding report."""
import json, os, sys, threading, glob
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.llm import load_env, chat, parse_json
from taskcat import sentence_schema as S
load_env()
inp, model, out = sys.argv[1], sys.argv[2], sys.argv[3]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 10**9; W = int(sys.argv[5]) if len(sys.argv) > 5 else 8
os.makedirs(out, exist_ok=True)
rows = [json.loads(l) for l in open(inp)][:N]
lock = threading.Lock(); usage_tot = {"prompt_tokens": 0, "completion_tokens": 0}
MAX_IN = int(os.environ.get("MAX_IN", 0)); MAX_OUT = int(os.environ.get("MAX_OUT", 0))
for f in glob.glob(os.path.join(os.path.dirname(out.rstrip("/")), "*", "*.json")):
    try: j = json.load(open(f))
    except Exception: continue
    if isinstance(j, dict) and j.get("model") == model:
        for k in usage_tot: usage_tot[k] += (j.get("usage") or {}).get(k, 0) or 0
def work(r):
    p = os.path.join(out, r["dbid"] + ".json")
    if os.path.exists(p): return
    if (MAX_IN and usage_tot["prompt_tokens"] >= MAX_IN) or (MAX_OUT and usage_tot["completion_tokens"] >= MAX_OUT): return
    try:
        content, usage = chat(S.messages(r["title"] or "", r["passage"]), model, schema=S.SCHEMA, schema_name="task_mentions_s",
                              reasoning_effort=os.environ.get("REASONING") or None,
                              service_tier=os.environ.get("SERVICE_TIER", "flex") or None)
        obj = parse_json(content); mention, stat = S.to_mention(obj, r["passage"])
        json.dump({"dbid": r["dbid"], "model": model, "schema": "v0.4-sentence", "parsed_s": obj, "parsed": mention,
                   "grounding": stat, "usage": usage}, open(p, "w"))
        with lock:
            for k in usage_tot: usage_tot[k] += usage.get(k, 0) or 0
    except Exception as e:
        json.dump({"dbid": r["dbid"], "model": model, "error": str(e)[:800]}, open(p + ".err", "w"))
with ThreadPoolExecutor(W) as ex: list(ex.map(work, rows))
print("usage", usage_tot)
