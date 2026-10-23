"""Build NuExtract3 fine-tuning rows from silver labels: {dbid, prompt, template, target_json, n_tokens}.
Usage (beast, venv-train python for tokenizer): build_train_data.py PASSAGES SILVER_DIR OUT.jsonl"""
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.template import TEMPLATE_V2, TEMPLATE_V2_STR, nuextract_document, to_v2
from taskcat.validate import clean
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("numind/NuExtract3")
pas = {json.loads(l)["dbid"]: json.loads(l) for l in open(sys.argv[1])}
n = 0; stats = {"rows": 0, "no_tasks": 0, "skipped_unparsed": 0}
with open(sys.argv[3], "w") as fo:
    for f in sorted(glob.glob(os.path.join(sys.argv[2], "*.json"))):
        j = json.load(open(f)); r = pas.get(j["dbid"])
        if r is None: continue
        if j.get("parsed") is None: stats["skipped_unparsed"] += 1; continue
        obj = to_v2(clean(j["parsed"], r["passage"]))
        tgt = json.dumps(obj, ensure_ascii=False)
        prompt = nuextract_document(r["title"] or "", r["passage"])
        text = tok.apply_chat_template([{"role": "user", "content": prompt}], template=TEMPLATE_V2_STR, tokenize=False,
                                       add_generation_prompt=True, enable_thinking=False)
        nt = len(tok(text, add_special_tokens=False)["input_ids"]) + len(tok(tgt, add_special_tokens=False)["input_ids"]) + 1
        fo.write(json.dumps({"dbid": j["dbid"], "prompt": prompt, "template": TEMPLATE_V2_STR, "target_json": tgt,
                             "n_tokens": nt}, ensure_ascii=False) + "\n")
        stats["rows"] += 1; stats["no_tasks"] += not obj.get("tasks")
print(stats)
