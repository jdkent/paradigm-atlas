"""Build extractor input passages for sampled papers (runs on beast, reads ns-pond texts)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.sections import select_task_passages, render
D = "/data/alejandro/projects/ns-pond/data"
man = {r["dbid"]: r for r in map(json.loads, open("data/manifest.jsonl"))}
splits = json.load(open("data/sample_splits.json"))
budget = int(os.environ.get("BUDGET", 12000))
for split in sys.argv[1:]:
    with open(f"data/passages_{split}.jsonl", "w") as fo:
        for d in splits[split]:
            r = man.get(d)
            if not r or not r.get("best_source"):
                continue
            text = open(f"{D}/{d}/processed/{r['best_source']}/text.txt", errors="replace").read()
            spans = select_task_passages(text, budget_chars=budget)
            passage, omap = render(text, spans)
            fo.write(json.dumps({"dbid": d, "pmid": r.get("pmid"), "pmcid": r.get("pmcid"), "doi": r.get("doi"),
                                 "title": r.get("title"), "authors": r.get("authors"), "journal": r.get("journal"),
                                 "year": r.get("year"), "source": r["best_source"], "passage": passage,
                                 "omap": omap, "text_len": len(text)}) + "\n")
