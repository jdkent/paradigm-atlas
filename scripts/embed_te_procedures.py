"""Embed TaskExtractor mentions' procedure text with the task name/paradigm terms masked (route B input).
Runs on beast GPU. Output: data/te_proc_emb.npy + data/te_proc_meta.jsonl"""
import json, os, re, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.lexicon import Lexicon
L = Lexicon()
rows = [json.loads(l) for l in open("data/te_tasks.jsonl")]
rows = [r for r in rows if r["kind"] != "none"]
BIG = re.compile("|".join(sorted({p.pattern for p, k, s in L.patterns} |
                               {r"\b" + re.escape(ph) + r"\b" for ph, k, v, s in L.entries if len(ph) > 5},
                               key=len, reverse=True)), re.I)
def mask(text, name):
    if not text: return ""
    for v in sorted({name or ""} | {re.sub(r"\s*\([^)]*\)", "", name or "")}, key=len, reverse=True):
        if len(v) > 3: text = re.sub(re.escape(v), "[TASK]", text, flags=re.I)
    return BIG.sub("[TASK]", text)
texts, meta = [], []
for r in rows:
    conds = r.get("Conditions") or []
    conds = "; ".join(c if isinstance(c, str) else json.dumps(c) for c in conds)[:400]
    t = f"{r.get('TaskDescription') or ''} {r.get('DesignDetails') or ''} Conditions: {conds}"
    texts.append(mask(t, r.get("TaskName"))[:2000])
    meta.append({"dbid": r["dbid"], "idx": r["idx"], "name": r.get("TaskName")})
from sentence_transformers import SentenceTransformer
m = SentenceTransformer(sys.argv[1] if len(sys.argv) > 1 else "Qwen/Qwen3-Embedding-0.6B", device="cuda")
m.max_seq_length = 512
E = m.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True)
np.save("data/te_proc_emb.npy", E.astype(np.float16))
with open("data/te_proc_meta.jsonl", "w") as f:
    for x, t in zip(meta, texts): f.write(json.dumps({**x, "masked": t[:500]}) + "\n")
print(E.shape)
