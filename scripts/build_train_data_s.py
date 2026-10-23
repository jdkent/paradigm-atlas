"""Student (v4, sentence-index) training rows from consensus silver. Usage: PASSAGES CONSENSUS_DIR OUT.jsonl
Each consensus file -> clean_for_student (grounded labels only) -> LIST row + one DETAIL row per task."""
import json, os, sys, glob, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.sentence_schema import clean_for_student
from taskcat import template_s as T
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("numind/NuExtract3")
pas = {}
for f in sys.argv[1].split(","):
    for l in open(f): r = json.loads(l); pas[r["dbid"]] = r
def ntok(prompt, tmpl, tgt):
    text = tok.apply_chat_template([{"role": "user", "content": prompt}], template=tmpl, tokenize=False,
                                   add_generation_prompt=True, enable_thinking=False)
    return len(tok(text, add_special_tokens=False)["input_ids"]) + len(tok(tgt, add_special_tokens=False)["input_ids"]) + 1
rows = []; st = {"papers": 0, "list": 0, "detail": 0}
for d in sys.argv[2].split(","):
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        j = json.load(open(f)); r = pas.get(j["dbid"])
        if r is None or not j.get("parsed_s"): continue
        tgt = clean_for_student(j["parsed_s"], r["passage"]); st["papers"] += 1
        for kind, prompt, tmpl, tj in T.rows_for(j["dbid"], r["title"] or "", r["passage"], tgt):
            rows.append({"dbid": j["dbid"], "kind": kind, "prompt": prompt, "template": tmpl, "target_json": tj,
                         "n_tokens": ntok(prompt, tmpl, tj)}); st[kind] += 1
random.Random(0).shuffle(rows)
with open(sys.argv[3], "w") as fo:
    for x in rows: fo.write(json.dumps(x, ensure_ascii=False) + "\n")
print(st, "over6k", sum(x["n_tokens"] > 6000 for x in rows), "mean tokens", sum(x["n_tokens"] for x in rows) // max(1, len(rows)))
