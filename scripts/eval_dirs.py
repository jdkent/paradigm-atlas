"""Usage: eval_dirs.py PASSAGES REF_DIR PRED_DIR [PRED_DIR...]"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.evaluate import evaluate, load_dir
from taskcat.validate import check
pas = {json.loads(l)["dbid"]: json.loads(l)["passage"] for l in open(sys.argv[1])}
ref = load_dir(sys.argv[2])
for d in sys.argv[3:]:
    pred = load_dir(d)
    common = set(pred) & set(ref)
    g = [check(pred[x], pas[x])[0] for x in common]
    gr = sum(s["grounded"] for s in g) / max(1, sum(s["verbatim"] for s in g))
    import glob
    nfiles = len(glob.glob(os.path.join(d, "*.json")))
    res = evaluate({k: pred[k] for k in common}, {k: ref[k] for k in common}, pas)
    print(os.path.basename(d.rstrip("/")), f"parsed={len(pred)}/{nfiles} grounding={gr:.3f}", json.dumps(res))
