"""Passages for the Europe PMC behavioral-psychology corpus (data/psych/<pmcid>/text.txt)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.sections import select_task_passages, render
root = sys.argv[1]; out = sys.argv[2]
n = 0
with open(out, "w") as fo:
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d, "text.txt")
        if not os.path.exists(p): continue
        text = open(p, errors="replace").read()
        if len(text) < 6000: continue
        spans = select_task_passages(text, budget_chars=12000)
        passage, omap = render(text, spans)
        title = text.split("\n", 1)[0].lstrip("# ").strip()
        fo.write(json.dumps({"dbid": d, "pmid": None, "pmcid": d, "title": title, "source": "epmc_jats",
                             "passage": passage, "omap": omap, "text_len": len(text)}) + "\n"); n += 1
print(n)
