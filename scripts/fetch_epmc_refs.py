"""Fetch Europe PMC reference lists for all manifest PMIDs into data/cache/epmc_refs (resumable)."""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat import citations as C
import requests
C.CACHE = sys.argv[2]
pm = [r["pmid"] for r in map(json.loads, open(sys.argv[1])) if r.get("pmid")]
pm = [p for p in pm if not os.path.exists(os.path.join(C.CACHE, f"{p}.json"))]
print("to fetch", len(pm), flush=True)
s = requests.Session()
def go(p):
    try: C.fetch_references(p, s)
    except Exception as e: print("ERR", p, e, flush=True)
with ThreadPoolExecutor(6) as ex:
    for i, _ in enumerate(ex.map(go, pm)):
        if i % 2000 == 0: print(i, time.strftime("%H:%M:%S"), flush=True)
