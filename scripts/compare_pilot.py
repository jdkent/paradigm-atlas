"""Compare silver-label pilot across models: parse rate, grounding, enum validity, task counts, tokens."""
import json, os, sys, glob, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.validate import check
pas = {json.loads(l)["dbid"]: json.loads(l) for l in open(sys.argv[1])}
for d in sys.argv[2:]:
    agg = collections.Counter(); ung = []; names = {}
    files = glob.glob(f"{d}/*.json"); errs = glob.glob(f"{d}/*.err")
    for f in files:
        j = json.load(open(f)); p = pas[j["dbid"]]["passage"]
        if j.get("parsed") is None: agg["unparsed"] += 1; continue
        s, u = check(j["parsed"], p); agg.update(s); ung += u
        agg["prompt_tok"] += j["usage"].get("prompt_tokens", 0) or 0; agg["compl_tok"] += j["usage"].get("completion_tokens", 0) or 0
        names[j["dbid"]] = [(t.get("name"), t.get("entity_kind")) for t in j["parsed"].get("tasks") or []]
    print(f"== {os.path.basename(d)} files={len(files)} errs={len(errs)} grounding={agg['grounded']}/{agg['verbatim']}="
          f"{agg['grounded']/max(1,agg['verbatim']):.3f} bad_enum={agg['bad_enum']} extra={agg['extra_key']} tasks={agg['n_tasks']} "
          f"tok={agg['prompt_tok']}/{agg['compl_tok']}")
    for pth, v in ung[:8]: print("   UNGROUNDED", pth, repr(v)[:100])
    json.dump(names, open(f"{d}.names.json", "w"))
