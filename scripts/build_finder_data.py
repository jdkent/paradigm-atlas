"""Compact TaskCards for the Task Finder page -> data/finder.json"""
import json, sys, collections
sys.path.insert(0, '.')
files = sys.argv[1:]
TL = {"experimental_task", "passive_stimulation", "naturalistic", "localizer", "neuropsychological_test", "resting_state"}
rows, seen = [], set()
for f in files:
    for c in map(json.loads, open(f)):
        if c["entity_kind"] not in TL: continue
        key = (c["dbid"], (c["name"] or "").lower())
        if key in seen: continue
        seen.add(key)
        I, F = c["identity"], c["facets"]
        conds = [{"n": x["name"][:60], "a": x["atoms"][:4]} for x in c["conditions"][:8]]
        rows.append({
            "p": c.get("pmid"), "pc": c.get("pmcid"), "t": (c.get("title") or "")[:160], "y": str(c.get("year") or "")[:4],
            "j": (c.get("journal") or "")[:60], "co": c.get("corpus"), "n": (c["name"] or "")[:80], "k": c["entity_kind"],
            "ct": I["canonical_task"], "cn": I["canonical_name"], "fa": I["family"], "st": I["stem"],
            "q": [q["text"] for q in I["qualifiers"] if q["axis"] != "other"][:4],
            "sk": sorted({s["value"] for s in F["stimulus_kind"]}), "sm": F["stimulus_modality"], "af": F["stimulus_affect"],
            "rk": F["response_kind"], "re": F["response_effector"], "dt": F["design_type"], "ju": F["judgment"][:4],
            "ms": F["measures"], "ax": F["manipulation_axes"], "ss": F["stimulus_sets"][:2],
            "ca": sorted({a.split(":")[0] for x in c["conditions"] for a in x["atoms"]}), "cd": conds,
            "or": c["lineage"]["origin_refs"][:3], "sa": (c["authors"][-1]["last"] if c["authors"] else None),
        })
json.dump(rows, open("data/finder.json", "w"), separators=(",", ":"))
print(len(rows), "rows", round(len(json.dumps(rows, separators=(',', ':'))) / 1e6, 2), "MB", collections.Counter(r["co"] for r in rows))
