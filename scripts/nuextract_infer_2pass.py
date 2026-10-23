"""Two-pass NuExtract inference: LIST pass per paper, then DETAIL pass per listed task.
Usage: nuextract_infer_2pass.py PASSAGES MODEL PORT OUTDIR [N]  -> OUTDIR/<dbid>.json with parsed={"tasks":[...]}"""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat import template as T
inp, model, port, out = sys.argv[1:5]
N = int(sys.argv[5]) if len(sys.argv) > 5 else 10**9
os.makedirs(out, exist_ok=True)
rows = [json.loads(l) for l in open(inp)][:N]
S = requests.Session()
def call(doc, tmpl, max_tokens):
    body = {"model": model, "messages": [{"role": "user", "content": doc}], "temperature": 0, "max_tokens": max_tokens,
            "chat_template_kwargs": {"template": tmpl, "enable_thinking": False}}
    j = S.post(f"http://127.0.0.1:{port}/v1/chat/completions", json=body, timeout=900).json()
    txt = j["choices"][0]["message"]["content"]
    try: return json.loads(txt), j.get("usage", {})
    except Exception: return None, j.get("usage", {})
def work(r):
    p = os.path.join(out, r["dbid"] + ".json")
    if os.path.exists(p): return
    t0 = time.time(); title = r["title"] or ""
    try:
        lst, u1 = call(T.nuextract_document(title, r["passage"]), T.TEMPLATE_LIST_STR, 1200)
        tasks = []; seen = set()
        for it in (lst or {}).get("tasks") or []:
            nm = (it or {}).get("name")
            if not nm or nm.lower() in seen: continue
            seen.add(nm.lower())
            det, _ = call(T.detail_document(title, r["passage"], nm), T.TEMPLATE_DETAIL_STR, 2500)
            det = det or {}
            det["name"] = det.get("name") or nm
            det["entity_kind"] = det.get("entity_kind") or it.get("entity_kind")
            det["setting"] = det.get("setting") or it.get("setting")
            tasks.append(det)
        json.dump({"dbid": r["dbid"], "model": model, "parsed": {"tasks": tasks}, "list": lst, "secs": time.time() - t0},
                  open(p, "w"))
    except Exception as e:
        json.dump({"dbid": r["dbid"], "error": repr(e)[:500]}, open(p + ".err", "w"))
with ThreadPoolExecutor(int(os.environ.get("CONC", 12))) as ex: list(ex.map(work, rows))
