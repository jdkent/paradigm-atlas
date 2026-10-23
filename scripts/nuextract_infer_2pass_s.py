"""Two-pass inference for the sentence-index student (v4). Usage: PASSAGES MODEL PORT OUTDIR [N]
Saves parsed_s (student output) and parsed (converted v0.2 TaskMention with grounded text)."""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat import template_s as T, sentence_schema as S
inp, model, port, out = sys.argv[1:5]; N = int(sys.argv[5]) if len(sys.argv) > 5 else 10**9
os.makedirs(out, exist_ok=True); Sess = requests.Session()
def call(doc, tmpl, mx):
    body = {"model": model, "messages": [{"role": "user", "content": doc}], "temperature": 0, "max_tokens": mx,
            "chat_template_kwargs": {"template": tmpl, "enable_thinking": False}}
    j = Sess.post(f"http://127.0.0.1:{port}/v1/chat/completions", json=body, timeout=900).json()
    try: return json.loads(j["choices"][0]["message"]["content"])
    except Exception: return None
def work(r):
    p = os.path.join(out, r["dbid"] + ".json")
    if os.path.exists(p): return
    t0 = time.time(); title = r["title"] or ""
    try:
        lst = call(T.document(title, r["passage"]), T.LIST_STR, 1200) or {}
        tasks, seen = [], set()
        for it in lst.get("tasks") or []:
            nm = (it or {}).get("name") or {}
            if not nm.get("text") or nm["text"].lower() in seen: continue
            seen.add(nm["text"].lower())
            det = call(T.detail_document(title, r["passage"], {"text": nm["text"], "sentence": nm.get("sentence")}), T.DETAIL_STR, 2000) or {}
            det["name"] = det.get("name") or nm
            det["entity_kind"] = det.get("entity_kind") or it.get("entity_kind"); det["setting"] = det.get("setting") or it.get("setting")
            tasks.append(det)
        obj = {"tasks": tasks}; mention, stat = S.to_mention(obj, r["passage"])
        json.dump({"dbid": r["dbid"], "model": model, "parsed_s": obj, "parsed": mention, "grounding": stat, "secs": time.time() - t0}, open(p, "w"))
    except Exception as e:
        json.dump({"dbid": r["dbid"], "error": repr(e)[:500]}, open(p + ".err", "w"))
rows = [json.loads(l) for l in open(inp)][:N]
with ThreadPoolExecutor(int(os.environ.get("CONC", 24))) as ex: list(ex.map(work, rows))
