"""H1: how much of the raw task-name long tail maps onto Cognitive Atlas tasks?"""
import json, re, collections, sys
import numpy as np
from rapidfuzz import process, fuzz
from sentence_transformers import SentenceTransformer

def norm(s):
    s = (s or "").lower()
    s = re.sub(r"\([^)]*\)", " ", s)          # drop parentheticals (acronyms)
    s = s.replace("–", "-").replace("/", " ")
    s = re.sub(r"\b(task|paradigm|test|experiment|procedure|fmri)\b", " ", s)
    s = re.sub(r"[-_]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

rows = [json.loads(l) for l in open("data/taskextractor/te_tasks.jsonl")]
raw = collections.Counter((r.get("TaskName") or "").strip() for r in rows if r["kind"] != "none")
ca = json.load(open("/home/jdkent/projects/buildCogAtlas/data/tasks.json"))
ca_names = {}
for t in ca:
    ca_names[norm(t["name"])] = t["name"]
    for a in re.split(r"[;,]", t.get("alias") or ""):
        if a.strip() and len(a.strip()) > 2:
            ca_names[norm(a)] = t["name"]
keys = list(ca_names)

normed = collections.Counter()
for n, c in raw.items(): normed[norm(n)] += c
print("raw unique", len(raw), "normalized unique", len(normed))
tot = sum(normed.values())
exact = sum(c for n, c in normed.items() if n in ca_names)
print(f"exact-after-norm to CA: {exact/tot:.3f} of mentions")

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
names = list(normed)
E = model.encode(names, batch_size=256, normalize_embeddings=True, show_progress_bar=False)
K = model.encode(keys, batch_size=256, normalize_embeddings=True, show_progress_bar=False)
S = E @ K.T
best = S.argmax(1); bs = S.max(1)
for thr in (0.95, 0.9, 0.85, 0.8, 0.75, 0.7):
    m = sum(normed[n] for n, s in zip(names, bs) if s >= thr)
    u = sum(1 for s in bs if s >= thr)
    print(f"emb>= {thr}: {m/tot:.3f} of mentions, {u/len(names):.3f} of unique names")
np.save("data/taskextractor/name_emb_minilm.npy", E)
out = [{"name": n, "count": normed[n], "ca": ca_names[keys[b]], "ca_key": keys[b], "sim": float(s)} for n, b, s in zip(names, best, bs)]
out.sort(key=lambda x: -x["count"])
json.dump(out, open("data/taskextractor/name_to_ca_minilm.json", "w"), indent=0)
# sample of mid-similarity for eyeballing
import random; random.seed(0)
for band in [(0.85, 0.9), (0.75, 0.8), (0.6, 0.7)]:
    samp = [o for o in out if band[0] <= o["sim"] < band[1]]
    print("BAND", band, len(samp))
    for o in random.sample(samp, min(12, len(samp))): print(f"  {o['sim']:.2f} {o['name']!r} -> {o['ca']!r}")
