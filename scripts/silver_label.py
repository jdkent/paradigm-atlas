"""Silver-label passages with an LLM via the gateway. Usage: silver_label.py PASSAGES.jsonl MODEL OUTDIR [N] [WORKERS]"""
import json, os, sys, threading
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.llm import load_env, chat, parse_json
from taskcat.template import labeler_messages, TEMPLATE_V2
from taskcat.jsonschema_from_template import to_schema
SCHEMA = None if os.environ.get("NO_SCHEMA") else to_schema(TEMPLATE_V2)   # strict structured output by default
load_env()
inp, model, out = sys.argv[1], sys.argv[2], sys.argv[3]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 10**9
W = int(sys.argv[5]) if len(sys.argv) > 5 else 8
os.makedirs(out, exist_ok=True)
rows = [json.loads(l) for l in open(inp)][:N]
lock = threading.Lock(); usage_tot = {"prompt_tokens": 0, "completion_tokens": 0}
# Hard budget across all runs of this model: sum usage already on disk under data/silver/*/
MAX_IN = int(os.environ.get("MAX_IN", 0)); MAX_OUT = int(os.environ.get("MAX_OUT", 0))
import glob as _g
for f in _g.glob(os.path.join(os.path.dirname(out.rstrip("/")), "*", "*.json")):
    try:
        j = json.load(open(f))
    except Exception:
        continue
    if isinstance(j, dict) and j.get("model") == model:
        for k in usage_tot: usage_tot[k] += (j.get("usage") or {}).get(k, 0) or 0
print("prior usage for", model, usage_tot, flush=True)
def work(r):
    p = os.path.join(out, r["dbid"] + ".json")
    if os.path.exists(p):
        return
    if (MAX_IN and usage_tot["prompt_tokens"] >= MAX_IN) or (MAX_OUT and usage_tot["completion_tokens"] >= MAX_OUT):
        return
    try:
        content, usage = chat(labeler_messages(r["title"] or "", r["passage"]), model, schema=SCHEMA, schema_name="task_mentions")
        obj = parse_json(content)
        json.dump({"dbid": r["dbid"], "model": model, "raw": content, "parsed": obj, "usage": usage}, open(p, "w"))
        with lock:
            for k in usage_tot: usage_tot[k] += usage.get(k, 0) or 0
    except Exception as e:
        json.dump({"dbid": r["dbid"], "model": model, "error": str(e)}, open(p + ".err", "w"))
with ThreadPoolExecutor(W) as ex:
    list(ex.map(work, rows))
print("usage", usage_tot)
