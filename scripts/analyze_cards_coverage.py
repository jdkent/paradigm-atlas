"""Coverage of canonical identity across card sets, by corpus; residue clustering for inventory growth.
Usage: analyze_cards_coverage.py CARDS.jsonl [CARDS2.jsonl ...]"""
import json, sys, collections, re
import numpy as np
cards = [json.loads(l) for f in sys.argv[1:] for l in open(f)]
TASKLIKE = {"experimental_task", "passive_stimulation", "naturalistic", "localizer", "neuropsychological_test"}
by = collections.defaultdict(list)
for c in cards: by[c.get("corpus", "?")].append(c)
for corp, cs in by.items():
    tl = [c for c in cs if c["entity_kind"] in TASKLIKE]
    lab = [c for c in tl if c["identity"]["canonical_task"]]
    routes = collections.Counter((c["identity"]["route"] or "none").split(":")[0] for c in tl)
    print(f"[{corp}] cards {len(cs)} task-like {len(tl)} canonical coverage {len(lab)/max(1,len(tl)):.3f} routes {dict(routes)}")
    print("   kinds", collections.Counter(c["entity_kind"] for c in cs).most_common())
    print("   top canonical", collections.Counter(c["identity"]["canonical_name"] for c in lab).most_common(15))
    res = [c for c in tl if not c["identity"]["canonical_task"]]
    if len(res) > 30:
        from sentence_transformers import SentenceTransformer
        from sklearn.cluster import AgglomerativeClustering
        M = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        texts = [f"{c['name']}. {c.get('description') or ''}" for c in res]
        X = M.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        cl = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average", distance_threshold=0.45).fit(X)
        g = collections.defaultdict(list)
        for c, l in zip(res, cl.labels_): g[l].append(c)
        big = sorted(g.values(), key=lambda v: -len({c["dbid"] for c in v}))
        print(f"   residue {len(res)} -> clusters with >=3 papers:")
        for v in big[:40]:
            if len({c['dbid'] for c in v}) < 3: break
            print(f"     {len({c['dbid'] for c in v}):3d}p | " + " / ".join(collections.Counter((c['name'] or '').lower() for c in v).most_common(1)[0][0] for _ in [0]) +
                  " | e.g. " + "; ".join(sorted({c['name'] or '' for c in v})[:4])[:150])
