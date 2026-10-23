"""H3: task-passage selection keeps the task evidence spans while cutting most of the text.
Uses astra records: task evidence spans (exact offsets into text.txt) as ground truth."""
import re, json, glob, os, sys, statistics, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.sections import select_task_passages, split_sections
RUN = "/home/jdkent/projects/StudyIESchema/pondie/pubget-astra-medium-100-results-20261008/runs/pubget_astra_medium_100"
budget = int(sys.argv[1]) if len(sys.argv) > 1 else 14000
def spans_of(f):
    ev = (f or {}).get("evidence") or {}
    return [s for st in ev.get("sets") or [] for s in st.get("spans") or []]
cov_name, cov_all, frac, n_tasks = [], [], [], 0
miss = collections.Counter()
for f in sorted(glob.glob(f"{RUN}/records/*.extraction.json")):
    dbid = os.path.basename(f).split(".")[0]
    text = open(f"{RUN}/corpus/{dbid}/processed/pubget/text.txt").read()
    rec = json.load(open(f)); tasks = rec.get("tasks") or []
    if not tasks: continue
    sel = select_task_passages(text, budget_chars=budget)
    inside = lambda s: any(a <= s["start_char"] and s["end_char"] <= b + 5 for a, b in sel)
    frac.append(sum(b - a for a, b in sel) / len(text))
    for t in tasks:
        if os.environ.get("NOREST") and re.search(r"rest", (t.get("name") or {}).get("value") or "", re.I): continue
        n_tasks += 1
        ns = spans_of(t.get("name")) + spans_of(t.get("description"))
        alls = [s for k in ("name","description","instructions","stimuli","design_type","references","performance_measures") for s in spans_of(t.get(k))]
        if ns: cov_name.append(any(inside(s) for s in ns))
        if alls: cov_all.append(sum(inside(s) for s in alls) / len(alls))
        if ns and not any(inside(s) for s in ns):
            secs = split_sections(text)
            for s in ns[:1]:
                z = [x for x in secs if x.start <= s["start_char"] < x.end]
                miss[(z[-1].zone, z[-1].heading[:40]) if z else ("?", "?")] += 1
print(f"budget={budget} tasks={n_tasks} name/desc-span covered={statistics.mean(cov_name):.3f} "
      f"mean frac of all task spans covered={statistics.mean(cov_all):.3f} text kept={statistics.mean(frac):.3f}")
print("misses by (zone, heading):", miss.most_common(15))
