"""Consensus of 2-3 sentence-indexed (v0.4) extractions of the same passage.

Protocol (user, 2026-10-09): run the labeler twice; where the runs MEANINGFULLY disagree, run a third and take the
majority; multi-valued fields are unioned (appended, de-duplicated).
- Tasks are aligned across runs by name similarity (taskcat.evaluate.align), anchored by the name's sentence.
- Meaningful disagreement = consumption-relevant (user rule): task inventory differs; or for an aligned task the
  gate category, setting, lexicon-canonical task, design type, a shared citation's role CATEGORY
  (lineage / stimulus_set / other) or a shared condition's kind category differs (null vs value counts).
- Single-choice fields: majority over available runs; with 2 runs that disagree and no 3rd -> None (abstain).
- Multi-valued fields (judgment, feedback, citation roles, sentence-index lists, stimuli, conditions, measures,
  factor levels, citations): union, de-duplicated by normalized text (or index).
"""
import collections, re
from .validate import squash

SINGLE = ["entity_kind", "setting"]
SINGLE_DESIGN = ["type", "adaptive"]
MIN_FIELD_CONFLICTS = 2


def _txt(v):
    return (v or {}).get("text") if isinstance(v, dict) else v


def _plain(t):  # align() expects plain 'name' strings
    return {**t, "name": _txt(t.get("name"))}


def _vote(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    c = collections.Counter(map(repr, vals)).most_common()
    if len(c) > 1 and c[0][1] == c[1][1]:
        return None                                   # tie -> abstain
    return next(v for v in vals if repr(v) == c[0][0])


def _key(x):
    return squash(_txt(x) or "") if not isinstance(x, (int, str)) or isinstance(x, str) else x


def _union(lists, key=_key):
    out, seen = [], set()
    for l in lists:
        for x in l or []:
            k = key(x)
            if k in (None, "") or k in seen:
                continue
            seen.add(k); out.append(x)
    return out


def _union_by(lists, field):
    return _union(lists, key=lambda x: squash(_txt(x.get(field)) or ""))


def _merge_citations(lists):
    """Union of markers; roles: majority over role CATEGORY (lineage / stimulus_set / other), then the union of the
    specific roles inside the winning category (e.g. task_origin + adapted_from are both lineage -> appended)."""
    by = {}
    for l in lists:
        for c in l or []:
            k = re.sub(r"[\s()\[\],;.]", "", (_txt(c.get("marker")) or "")).lower()
            if not k:
                continue
            by.setdefault(k, {"marker": c.get("marker"), "votes": []})["votes"].append(set(c.get("roles") or []))
    out = []
    for k, v in by.items():
        cats = collections.Counter(role_cat(r) for r in v["votes"] if r)
        if not cats:
            out.append({"marker": v["marker"], "roles": []}); continue
        top = cats.most_common()
        win = top[0][0] if len(top) == 1 or top[0][1] > top[1][1] else None      # tie across categories -> abstain
        roles = sorted(set().union(*[r for r in v["votes"] if role_cat(r) == win])) if win else []
        out.append({"marker": v["marker"], "roles": roles})
    return out


def align_runs(ta, tb, thr=70):
    """Greedy task alignment across runs: name similarity, OR same entity_kind and (same name sentence or
    instructions-sentence overlap >= .5) — the same task is often named differently by two runs."""
    from .evaluate import sim
    def score(a, b):
        s = sim(_txt(a.get("name")), _txt(b.get("name")))
        if a.get("entity_kind") == b.get("entity_kind"):
            na, nb = (a.get("name") or {}).get("sentence"), (b.get("name") or {}).get("sentence")
            ia, ib = set(a.get("instructions_sentences") or []), set(b.get("instructions_sentences") or [])
            if na and na == nb: s = max(s, 90)
            if ia and ib and len(ia & ib) / len(ia | ib) >= 0.5: s = max(s, 85)   # IDs compare as strings
        return s
    cand = sorted(((score(a, b), i, j) for i, a in enumerate(ta) for j, b in enumerate(tb)), reverse=True)
    used_a, used_b, pairs = set(), set(), []
    for sc, i, j in cand:
        if sc < thr: break
        if i in used_a or j in used_b: continue
        pairs.append((i, j)); used_a.add(i); used_b.add(j)
    return pairs


# ---- consumption-based projections: two values "disagree" only if downstream use differs ----
LINEAGE = {"task_origin", "adapted_from", "prior_use"}
def role_cat(roles):
    rs = set(roles or [])
    cats = {"lineage" if r in LINEAGE else ("stimulus_set" if r == "stimulus_set" else "other") for r in rs}
    return frozenset(cats) or None
GATE = {"experimental_task": "task", "passive_stimulation": "task", "naturalistic": "task", "localizer": "task",
        "resting_state": "rest", "neuropsychological_test": "neuropsych",
        "questionnaire_or_scale": "nontask", "intervention_or_training": "nontask"}
_LEX = None
def canon(label):
    """Lexicon canonical task for a {text,sentence} label (None if no match)."""
    global _LEX
    if _LEX is None:
        from .lexicon import Lexicon
        _LEX = Lexicon()
    t = _txt(label)
    m = _LEX.match(t) if t else None
    return m[0] if m else None
def _cond_kind_cat(k):
    return None if k is None else ("task" if k == "task_state" else "baseline")

PROJECTIONS = {   # field -> function(task) giving the consumption-relevant value
    "gate": lambda t: GATE.get(t.get("entity_kind")),
    # setting is consumed as in-scanner (Task) vs outside (Assessment): not_imaging == outside_imaging
    "setting": lambda t: {"during_imaging": "in", "both": "in", "outside_imaging": "out", "not_imaging": "out"}.get(t.get("setting")),
    "canonical": lambda t: canon(t.get("paradigm_term")) or canon(t.get("name")),
    "design_type": lambda t: (t.get("design") or {}).get("type") if (t.get("design") or {}).get("type") != "unknown" else None,
}


def task_conflicts(a, b):
    """List of consumption-relevant disagreements between two aligned tasks (null vs value counts)."""
    out = [f for f, proj in PROJECTIONS.items() if proj(a) != proj(b)]
    ca = {re.sub(r"[\s()\[\],;.]", "", (_txt(c.get("marker")) or "")).lower(): role_cat(c.get("roles")) for c in a.get("citations") or []}
    cb = {re.sub(r"[\s()\[\],;.]", "", (_txt(c.get("marker")) or "")).lower(): role_cat(c.get("roles")) for c in b.get("citations") or []}
    for k in set(ca) & set(cb):
        if k and ca[k] != cb[k]:
            out.append(f"citation_role:{k[:30]}")
    ka = {squash(_txt(c.get("name")) or ""): _cond_kind_cat(c.get("kind")) for c in a.get("conditions") or []}
    kb = {squash(_txt(c.get("name")) or ""): _cond_kind_cat(c.get("kind")) for c in b.get("conditions") or []}
    for k in set(ka) & set(kb):
        if k and ka[k] != kb[k]:
            out.append(f"condition_kind:{k[:30]}")
    return out


def needs_third(r1, r2):
    """(bool, reasons): True if two runs disagree in a way that changes downstream use."""
    t1, t2 = (r1 or {}).get("tasks") or [], (r2 or {}).get("tasks") or []
    pairs = align_runs(t1, t2)
    reasons = []
    if len(pairs) != len(t1) or len(pairs) != len(t2):
        reasons.append("task_inventory")
    for i, j in pairs:
        reasons += task_conflicts(t1[i], t2[j])
    return bool(reasons), reasons


def merge(runs):
    """runs: list of 2-3 v0.4 extraction dicts. Returns consensus dict + report."""
    runs = [r or {"tasks": []} for r in runs]
    base = runs[0]["tasks"]
    groups = [[t] for t in base]                       # task groups across runs, keyed by run-0 order
    extra = []
    for r in runs[1:]:
        ts = r["tasks"]
        pairs = dict(align_runs(ts, [g[0] for g in groups]))
        for i, t in enumerate(ts):
            if i in pairs:
                groups[pairs[i]].append(t)
            else:
                groups.append([t]); extra.append(_txt(t.get("name")))
    # with 3 runs a task needs >= 2 supporting runs (majority); with 2 agreeing runs every task is kept
    tasks, dropped = [], []
    for g in groups:
        if len(runs) >= 3 and len(g) < 2:
            dropped.append(_txt(g[0].get("name"))); continue
        D = [t.get("design") or {} for t in g]
        tasks.append({
            "name": _vote([t.get("name") for t in g]) or g[0].get("name"),
            "paradigm_term": _vote([t.get("paradigm_term") for t in g]),
            "entity_kind": _vote([t.get("entity_kind") for t in g]),
            "setting": _vote([t.get("setting") for t in g]),
            "description": next((t.get("description") for t in g if t.get("description")), None),
            "instructions_sentences": sorted(set(_union([t.get("instructions_sentences") for t in g], key=lambda x: x))),
            "judgment": sorted(set(_union([t.get("judgment") for t in g], key=lambda x: x))),
            "stimuli": _union_by([t.get("stimuli") for t in g], "content"),
            "response": _union([t.get("response") for t in g], key=lambda x: (x.get("effector"), x.get("kind"))),
            "conditions": _union_by([t.get("conditions") for t in g], "name"),
            "manipulated_factors": _union([t.get("manipulated_factors") for t in g], key=lambda x: (x.get("factor") or "").lower()),
            "design": {"type": _vote([d.get("type") for d in D]), "n_runs": _vote([d.get("n_runs") for d in D]),
                       "n_trials_sentences": sorted(set(_union([d.get("n_trials_sentences") for d in D], key=lambda x: x))),
                       "timing_sentences": sorted(set(_union([d.get("timing_sentences") for d in D], key=lambda x: x))),
                       "adaptive": "yes" if any(d.get("adaptive") == "yes" for d in D) else _vote([d.get("adaptive") for d in D])},
            "feedback": sorted(set(_union([t.get("feedback") for t in g], key=lambda x: x))),
            "measures": _union([t.get("measures") for t in g]),
            "software": _vote([t.get("software") for t in g]) or next((t.get("software") for t in g if t.get("software")), None),
            "citations": _merge_citations([t.get("citations") for t in g]),
            "modification_sentences": sorted(set(_union([t.get("modification_sentences") for t in g], key=lambda x: x))),
            "_support": len(g),
        })
    return {"tasks": tasks}, {"n_runs": len(runs), "groups": len(groups), "dropped_minority": dropped, "unmatched": extra}
