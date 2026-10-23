"""Export the canonical task inventory as a machine-readable ontology: schema/task_inventory_v3.json"""
import json, csv, collections, sys, os
sys.path.insert(0, '.')
from taskcat.lexicon import Lexicon, EXTENSIONS, HED_PATTERNS, BRAINMAP_EXT
from taskcat.decompose import STEM_OF, STEMS
L = Lexicon(); fam = lambda k: (L.family.get(k) or [None])[0]
HED = 'data/external/hed-task/data'
atlas = collections.defaultdict(list)
for r in csv.DictReader(open(f'{HED}/mappings/hed_task_to_atlas.tsv'), delimiter='\t'):
    if r['match_type'] in ('exact', 'close'): atlas[r['hedtsk_id']].append({"id": r['atlas_id'], "name": r['atlas_name'], "match": r['match_type']})
cogpo = collections.defaultdict(list)
for r in csv.DictReader(open(f'{HED}/mappings/hed_task_to_cogpo.tsv'), delimiter='\t'):
    k = r.get('hedtsk_id'); m = r.get('match_type')
    if k and m in ('exact', 'close'): cogpo[k].append({k2: r[k2] for k2 in r if k2.startswith('cogpo')} | {"match": m})
bm = collections.defaultdict(list)
for x in json.load(open('data/external/brainmap_crosswalk.json')):
    tgt = x.get('inventory_id') or (x.get('proposed_extension') or {}).get('id')
    if tgt: bm[tgt].append({"class": x['brainmap_class'], "match": x['match_type'], "first": x.get('first')})
origins = {o['task']: o['top_refs'] for o in json.load(open('data/taskextractor/discovered_origins.json'))}
conds = {s['task']: s for s in json.load(open('data/taskextractor/condition_schemas.json'))}
N = [json.loads(l) for l in open('data/taskextractor/te_normalized.jsonl')]
cnt = collections.Counter(r['canonical'] for r in N if r['canonical'])
pap = collections.defaultdict(set)
for r in N:
    if r['canonical']: pap[r['canonical']].add(r['dbid'])
out = []
for k, name in sorted(L.names.items(), key=lambda kv: (fam(kv[0]) or '', kv[1])):
    t = L.tasks.get(k, {})
    src = 'hed-task' if k.startswith('hedtsk_') else ('brainmap-derived' if k in BRAINMAP_EXT else 'corpus-extension')
    pats = HED_PATTERNS.get(k, []) + list((EXTENSIONS.get(k) or (None, None, []))[2])
    c = conds.get(k)
    out.append({"id": k, "name": name, "family": fam(k), "stem": STEM_OF.get(k, k), "source": src,
                "definition": t.get('short_definition'), "aliases": t.get('aliases', []),
                "variations": [{"id": v['variation_id'], "name": v['name']} for v in t.get('variations', [])],
                "inclusion_test": t.get('inclusion_test'), "patterns": pats,
                "crosswalk": {"cognitive_atlas": atlas.get(k, []), "cogpo": cogpo.get(k, []), "brainmap": bm.get(k, [])},
                "curated_references": [{"title": r.get('title'), "year": r.get('year'), "doi": (r.get('ids') or {}).get('doi'), "role": r.get('role')} for r in t.get('references', [])],
                "discovered_origin_refs": origins.get(k, [])[:5],
                "condition_schema": ({a: [v for v, _ in vs] for a, vs in c['axes'].items()} | {'_phases': [p for p, n in c['phases'] if n >= 0.1 * c['mentions']]}) if c else {},
                "corpus": {"mentions": cnt.get(k, 0), "papers": len(pap.get(k, ()))}})
json.dump({"version": "3.1", "date": "2026-10-09", "n_tasks": len(out),
           "families": sorted({x['family'] for x in out if x['family']}), "stems": STEMS, "tasks": out},
          open('schema/task_inventory_v3.json', 'w'), indent=1)
print(len(out), collections.Counter(x['source'] for x in out), os.path.getsize('schema/task_inventory_v3.json') // 1000, 'KB')
