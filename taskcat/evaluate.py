"""Compare predicted TaskMention extractions to reference extractions (per paper).

Task alignment: greedy on name similarity (rapidfuzz token_set_ratio on normalized names, or containment),
threshold 70. Then field agreement on aligned pairs.
"""
import json, re, collections
from rapidfuzz import fuzz
from .validate import clean, squash


def _n(s):
    s = (s or "").lower()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\b(the|a|an|task|paradigm|test)\b", " ", s)
    return re.sub(r"[^a-z0-9+]+", " ", s).strip()


def sim(a, b):
    a, b = _n(a), _n(b)
    if not a or not b:
        return 0
    if a in b or b in a:
        return 100
    return fuzz.token_set_ratio(a, b)


def align(pred, ref, thr=70):
    pairs, used = [], set()
    cand = sorted(((sim(p.get("name"), r.get("name")), i, j) for i, p in enumerate(pred) for j, r in enumerate(ref)),
                  reverse=True)
    pu = set()
    for s, i, j in cand:
        if s < thr:
            break
        if i in pu or j in used:
            continue
        pairs.append((i, j)); pu.add(i); used.add(j)
    return pairs


def _set(v):
    if v is None:
        return set()
    if isinstance(v, list):
        return {x for x in v if isinstance(x, str)}
    return {v}


def setf1(a, b):
    if not a and not b:
        return None
    tp = len(a & b)
    return 2 * tp / (len(a) + len(b)) if (a or b) else None


def fuzzy_setf1(a, b, thr=80):
    a, b = [squash(x) for x in a if x], [squash(x) for x in b if x]
    if not a and not b:
        return None
    if not a or not b:
        return 0.0
    ra = sum(any(fuzz.ratio(x, y) >= thr for y in b) for x in a) / len(a)
    rb = sum(any(fuzz.ratio(x, y) >= thr for y in a) for x in b) / len(b)
    return 2 * ra * rb / (ra + rb) if ra + rb else 0.0


def cit_norm(m):
    m = re.sub(r"[\s()\[\]]", "", m or "").lower()
    return m.replace("etal.", "etal").replace("&", "and")


FIELDS = {
    "entity_kind": lambda t: _set(t.get("entity_kind")),
    "setting": lambda t: _set(t.get("setting")),
    "design_type": lambda t: _set((t.get("design") or {}).get("type")),
    "judgment": lambda t: _set(t.get("judgment")),
    "stim_modality": lambda t: {s.get("modality") for s in t.get("stimuli") or [] if s.get("modality")},
    "resp_effector": lambda t: {s.get("effector") for s in t.get("response") or [] if s.get("effector")},
    "resp_kind": lambda t: {s.get("kind") for s in t.get("response") or [] if s.get("kind")},
    "feedback": lambda t: _set(t.get("feedback")),
    "cit_role": lambda t: {(cit_norm(c.get("marker")), c.get("role")) for c in t.get("citations") or []},
}
FUZZY = {
    "conditions": lambda t: [c.get("name") for c in t.get("conditions") or []],
    "stim_content": lambda t: [s.get("content") for s in t.get("stimuli") or []],
    "measures": lambda t: t.get("measures") or [],
    "citations": lambda t: [cit_norm(c.get("marker")) for c in t.get("citations") or []],
    "paradigm_term": lambda t: [t.get("paradigm_term")] if t.get("paradigm_term") else [],
}


def evaluate(preds, refs, passages):
    """preds/refs: {dbid: parsed obj}; passages: {dbid: passage}. Returns summary dict."""
    tot = collections.Counter(); fs = collections.defaultdict(list)
    for d, ref in refs.items():
        if d not in preds:
            continue
        P = (clean(preds[d], passages[d]) or {}).get("tasks") or []
        R = (clean(ref, passages[d]) or {}).get("tasks") or []
        pairs = align(P, R)
        tot["papers"] += 1; tot["pred"] += len(P); tot["ref"] += len(R); tot["tp"] += len(pairs)
        tot["empty_agree"] += (not P and not R)
        for i, j in pairs:
            for k, f in FIELDS.items():
                v = setf1(f(P[i]), f(R[j]))
                if v is not None:
                    fs[k].append(v)
            for k, f in FUZZY.items():
                v = fuzzy_setf1(f(P[i]), f(R[j]))
                if v is not None:
                    fs[k].append(v)
    p = tot["tp"] / max(1, tot["pred"]); r = tot["tp"] / max(1, tot["ref"])
    out = {"papers": tot["papers"], "task_P": round(p, 3), "task_R": round(r, 3),
           "task_F1": round(2 * p * r / max(1e-9, p + r), 3), "n_pred": tot["pred"], "n_ref": tot["ref"]}
    for k, v in fs.items():
        out[k] = round(sum(v) / len(v), 3)
    return out


def load_dir(d):
    import glob, os
    out = {}
    for f in glob.glob(os.path.join(d, "*.json")):
        j = json.load(open(f))
        if j.get("parsed") is not None:
            out[j["dbid"]] = j["parsed"]
    return out
