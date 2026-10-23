"""For every TaskExtractor task mention, find where its name occurs in the source text, collect the citation markers
in the sentence(s) around each occurrence (same paragraph, +-1 sentence), and resolve them with the XML
bibliography (or EPMC cache). Output JSONL: one row per (dbid, task idx) with resolved refs. Runs on beast."""
import json, os, re, sys, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.citations import find_citations, resolve_with_bib, resolve
D = "/data/alejandro/projects/ns-pond/data"
man = {r["dbid"]: r for r in map(json.loads, open("data/manifest.jsonl"))}
STOP = {"task", "paradigm", "test", "the", "a", "an", "of", "and", "fmri", "functional", "mri", "experiment"}
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")

def name_variants(name):
    n = re.sub(r"\s*\([^)]*\)", "", name or "").strip()
    out = {n}
    m = re.search(r"\(([A-Za-z0-9\-/]{2,10})\)", name or "")
    if m: out.add(m.group(1))                  # acronym
    toks = [t for t in re.findall(r"[A-Za-z0-9\-/']+", n) if t.lower() not in STOP]
    if len(toks) >= 2: out.add(" ".join(toks[:3]))
    return [v for v in out if len(v) >= 3]

def one(args):
    dbid, tasks = args
    r = man.get(dbid)
    if not r or not r.get("best_source"): return []
    try: text = open(f"{D}/{dbid}/processed/{r['best_source']}/text.txt", errors="replace").read()
    except Exception: return []
    cut = re.search(r"(?mi)^#*\s*(references|bibliography)\s*$", text)
    if cut: text = text[:cut.start()]
    bib = None
    if os.path.exists(f"data/bib/{dbid}.json"): bib = json.load(open(f"data/bib/{dbid}.json"))
    epmc = None
    if not bib and r.get("pmid") and os.path.exists(f"data/cache/epmc_refs/{r['pmid']}.json"):
        epmc = json.load(open(f"data/cache/epmc_refs/{r['pmid']}.json"))
    paras = text.split("\n")
    rows = []
    for idx, t, mid in tasks:
        vs = name_variants(t.get("TaskName"))
        markers = collections.Counter(); hits = 0; ctxs = {}
        for p in paras:
            if len(p) < 40 or not any(v.lower() in p.lower() for v in vs): continue
            sents = SENT.split(p)
            for i, s in enumerate(sents):
                if any(v.lower() in s.lower() for v in vs):
                    hits += 1
                    win = " ".join(sents[i:i + 2])
                    for m in find_citations(win):
                        markers[m] += 1; ctxs.setdefault(m, win.replace(m, " [CIT] ")[:600])
        refs = {}
        for m in markers:
            got = resolve_with_bib(m, bib) if bib else (resolve(m, epmc) if epmc else [])
            for g in got:
                key = g.get("pmid") or g.get("id") or g.get("doi") or f"{dbid}:{g.get('rid')}"
                refs[key] = {"pmid": g.get("pmid") or g.get("id"), "doi": g.get("doi"),
                             "first_author": g.get("first_author") or (g.get("authorString") or "").split(" ")[0],
                             "year": g.get("year") or g.get("pubYear"), "title": (g.get("title") or "")[:200],
                             "marker": m, "context": ctxs.get(m)}
        rows.append({"mid": mid, "dbid": dbid, "idx": idx, "name": t.get("TaskName"), "hits": hits,
                     "n_markers": len(markers), "bib": "xml" if bib else ("epmc" if epmc else None),
                     "refs": list(refs.values())})
    return rows

if __name__ == "__main__":
    by = collections.defaultdict(list)
    for l in open("data/te_tasks.jsonl"):
        t = json.loads(l)
        if t["kind"] != "none": by[t["dbid"]].append((t["idx"], t, t["mid"]))
    with ProcessPoolExecutor(32) as ex, open(sys.argv[1], "w") as fo:
        for rows in ex.map(one, list(by.items()), chunksize=40):
            for x in rows: fo.write(json.dumps(x) + "\n")
