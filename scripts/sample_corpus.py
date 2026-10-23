"""Stratified sample of ns-pond papers for silver labeling (train) and gold evaluation (held out).
Stratifies on normalized TaskExtractor task names so the long tail is represented; caps the head."""
import json, random, re, collections, glob, os
random.seed(13)
def norm(s):
    s = (s or "").lower(); s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\b(task|paradigm|test|experiment|fmri|functional|mri|scan|session)s?\b", " ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()
man = {r["dbid"]: r for r in map(json.loads, open("data/manifest.jsonl"))}
te = collections.defaultdict(list)
for l in open("data/taskextractor/te_tasks.jsonl"):
    r = json.loads(l)
    if r["kind"] != "none": te[r["dbid"]].append(norm(r.get("TaskName")))
    else: te.setdefault(r["dbid"], [])
astra = {os.path.basename(f).split(".")[0] for f in glob.glob("/home/jdkent/projects/StudyIESchema/pondie/pubget-astra-medium-100-results-20261008/runs/pubget_astra_medium_100/records/*.json")}
def ok(r):
    return r["best_source"] and r["sources"][r["best_source"]]["len"] > 8000 and r.get("pmid")
cands = [d for d, r in man.items() if ok(r) and d not in astra]
random.shuffle(cands)
def is_rest(names): return names and all("rest" in n for n in names)
def pick(n_target, cap, exclude, ace_frac=0.15, rest_frac=0.08, none_frac=0.05):
    out, cnt = [], collections.Counter(); n_rest = n_none = n_ace = 0
    for d in cands:
        if d in exclude: continue
        r = man[d]; names = te.get(d)
        ace = r["best_source"] in ("ace", "pdf")
        if ace and n_ace >= ace_frac * n_target: continue
        if names is None or names == []:
            if n_none >= none_frac * n_target: continue
            n_none += 1
        elif is_rest(names):
            if n_rest >= rest_frac * n_target: continue
            n_rest += 1
        else:
            if all(cnt[n] >= cap for n in names): continue
        for n in names or []: cnt[n] += 1
        n_ace += ace; out.append(d)
        if len(out) >= n_target: break
    return out, cnt
gold, _ = pick(150, 2, set())
train, cnt = pick(4000, 6, set(gold))
json.dump({"gold": gold, "train": train, "astra_heldout": sorted(astra)}, open("data/sample_splits.json", "w"), indent=0)
print("gold", len(gold), "train", len(train), "distinct TE names in train", len(cnt))
C = collections.Counter(man[d]["best_source"] for d in train); print(C)
