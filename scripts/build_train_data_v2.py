"""Two-pass fine-tuning rows: one LIST row per paper + one DETAIL row per task. Usage: PASSAGES SILVER_DIR OUT.jsonl"""
import json, os, sys, glob, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.template import TEMPLATE_LIST_STR, TEMPLATE_DETAIL_STR, nuextract_document, detail_document, to_v2
from taskcat.validate import clean
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("numind/NuExtract3")
pas = {json.loads(l)["dbid"]: json.loads(l) for l in open(sys.argv[1])}
def ntok(prompt, tmpl, tgt):
    text = tok.apply_chat_template([{"role": "user", "content": prompt}], template=tmpl, tokenize=False,
                                   add_generation_prompt=True, enable_thinking=False)
    return len(tok(text, add_special_tokens=False)["input_ids"]) + len(tok(tgt, add_special_tokens=False)["input_ids"]) + 1
rows = []; st = {"list": 0, "detail": 0}
for f in sorted(glob.glob(os.path.join(sys.argv[2], "*.json"))):
    j = json.load(open(f)); r = pas.get(j["dbid"])
    if r is None or j.get("parsed") is None: continue
    obj = to_v2(clean(j["parsed"], r["passage"])); title = r["title"] or ""
    tasks = [t for t in obj.get("tasks") or [] if t.get("name")]
    lst = {"tasks": [{"name": t["name"], "entity_kind": t.get("entity_kind"), "setting": t.get("setting")} for t in tasks]}
    p = nuextract_document(title, r["passage"]); tgt = json.dumps(lst, ensure_ascii=False)
    rows.append({"dbid": j["dbid"], "kind": "list", "prompt": p, "template": TEMPLATE_LIST_STR, "target_json": tgt,
                 "n_tokens": ntok(p, TEMPLATE_LIST_STR, tgt)}); st["list"] += 1
    for t in tasks:
        p = detail_document(title, r["passage"], t["name"]); tgt = json.dumps(t, ensure_ascii=False)
        rows.append({"dbid": j["dbid"], "kind": "detail", "prompt": p, "template": TEMPLATE_DETAIL_STR, "target_json": tgt,
                     "n_tokens": ntok(p, TEMPLATE_DETAIL_STR, tgt)}); st["detail"] += 1
random.Random(0).shuffle(rows)
with open(sys.argv[3], "w") as fo:
    for x in rows: fo.write(json.dumps(x, ensure_ascii=False) + "\n")
print(st, "over6k", sum(x["n_tokens"] > 6000 for x in rows), "total tokens", sum(x["n_tokens"] for x in rows))
