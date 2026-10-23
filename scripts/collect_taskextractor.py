"""Flatten TaskExtractor 1.1.0 outputs into one JSONL (one row per task mention)."""
import json, os, sys
D = sys.argv[1]; out = sys.argv[2]
n_docs = 0
with open(out, "w") as fo:
    for dbid in os.listdir(D):
        p = os.path.join(D, dbid)
        try:
            info = json.load(open(os.path.join(p, "info.json")))
            res = json.load(open(os.path.join(p, "results.json")))
        except Exception:
            continue
        if not isinstance(res, dict) or not isinstance(info, dict):
            continue
        n_docs += 1
        ids = info.get("identifiers", {})
        base = {"dbid": dbid, "pmid": ids.get("pmid"), "pmcid": ids.get("pmcid"), "doi": ids.get("doi"),
                "valid": info.get("valid"), "modality": res.get("Modality"),
                "objective": res.get("StudyObjective"), "exclude": res.get("Exclude")}
        for kind in ("fMRITasks", "BehavioralTasks"):
            for i, t in enumerate(res.get(kind) or []):
                if not isinstance(t, dict):
                    continue
                fo.write(json.dumps({**base, "kind": kind, "idx": i, **t}) + "\n")
        if not (res.get("fMRITasks") or res.get("BehavioralTasks")):
            fo.write(json.dumps({**base, "kind": "none"}) + "\n")
print("docs", n_docs)
