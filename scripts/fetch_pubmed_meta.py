"""Fetch PubMed records for all manifest PMIDs -> data/pubmed/meta_XXXX.jsonl (resumable by chunk)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat import pubmed as P
P.load_env()
pm = sorted({r["pmid"] for r in map(json.loads, open(sys.argv[1])) if r.get("pmid")})
out = sys.argv[2]; os.makedirs(out, exist_ok=True)
CH = 2000
for i in range(0, len(pm), CH):
    f = os.path.join(out, f"meta_{i // CH:04d}.jsonl")
    if os.path.exists(f): continue
    recs = P.efetch_records(pm[i:i + CH])
    with open(f + ".tmp", "w") as fo:
        for k, v in recs.items(): fo.write(json.dumps({"pmid": k, **v}) + "\n")
    os.rename(f + ".tmp", f); print(i, len(recs), flush=True)
