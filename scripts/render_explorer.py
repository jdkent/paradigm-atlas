"""Render site/paradigm_atlas.html from data/explorer.json (+ condition schemas) and data/explorer_hyps.json.
Run after scripts/build_explorer_data.py and scripts/condition_schemas.py."""
import json
E = json.load(open('data/explorer.json'))
S = {s['task']: s for s in json.load(open('data/taskextractor/condition_schemas.json'))}
for t in E['tasks']:
    s = S.get(t['id'])
    t['conditions'] = {"axes": sorted([[a, vs] for a, vs in s['axes'].items()], key=lambda x: -sum(c for _, c in x[1])),
                       "phases": s['phases'], "per_mention": s['conds_per_mention'], "top_names": s['top_condition_names'][:10]} if s else None
html = open('scripts/explorer_template.html').read().replace('__DATA__', json.dumps(E).replace('</', '<\\/')) \
    .replace('__HYPS__', json.dumps(json.load(open('data/explorer_hyps.json'))))
open('site/paradigm_atlas.html', 'w').write(html); print(len(html))
