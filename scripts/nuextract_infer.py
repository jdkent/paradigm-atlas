"""Run a vLLM-served NuExtract3 over passages. Usage: nuextract_infer.py PASSAGES MODEL PORT OUTDIR [--constrain] [N]"""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat import template as T
from taskcat.jsonschema_from_template import to_schema
inp, model, port, out = sys.argv[1:5]
constrain = "--constrain" in sys.argv
N = int([a for a in sys.argv[5:] if a.isdigit()][0]) if any(a.isdigit() for a in sys.argv[5:]) else 10**9
tmpl = getattr(T, os.environ.get("TEMPLATE_NAME", "TEMPLATE"))
TS = json.dumps(tmpl, ensure_ascii=False); SCHEMA = to_schema(tmpl)
os.makedirs(out, exist_ok=True)
rows = [json.loads(l) for l in open(inp)][:N]
def work(r):
    p = os.path.join(out, r["dbid"] + ".json")
    if os.path.exists(p): return
    body = {"model": model, "messages": [{"role": "user", "content": T.nuextract_document(r["title"] or "", r["passage"])}],
            "temperature": 0, "max_tokens": 3500,
            "chat_template_kwargs": {"template": TS, "enable_thinking": False}}
    if constrain: body["structured_outputs"] = {"json": SCHEMA}
    t0 = time.time()
    try:
        resp = requests.post(f"http://127.0.0.1:{port}/v1/chat/completions", json=body, timeout=900)
        j = resp.json(); txt = j["choices"][0]["message"]["content"]
        try: parsed = json.loads(txt)
        except Exception: parsed = None
        json.dump({"dbid": r["dbid"], "model": model, "raw": txt, "parsed": parsed, "usage": j.get("usage"),
                   "secs": time.time() - t0}, open(p, "w"))
    except Exception as e:
        json.dump({"dbid": r["dbid"], "error": repr(e)[:500]}, open(p + ".err", "w"))
with ThreadPoolExecutor(8) as ex: list(ex.map(work, rows))
