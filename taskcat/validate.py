"""Validate extractions against the TaskMention template: enum membership and verbatim grounding."""
import re
from .template import TEMPLATE

_WS = re.compile(r"\s+")


def squash(s):
    s = s.replace(" ", " ").replace(" ", " ")
    s = re.sub(r"\s*([()\[\],;:])\s*", r"\1", s)  # pubget adds spaces around punctuation
    return _WS.sub(" ", s).strip().lower()


def grounded(value, passage_sq):
    v = squash(value)
    return bool(v) and v in passage_sq


def _walk(tmpl, val, path, out):
    """Yield (path, kind, value) leaves; kind in verbatim|string|enum|multienum|integer."""
    if val is None:
        return
    if isinstance(tmpl, dict):
        if not isinstance(val, dict):
            out.append((path, "type_error", val)); return
        for k, t in tmpl.items():
            _walk(t, val.get(k), f"{path}.{k}", out)
        for k in val:
            if k not in tmpl:
                out.append((f"{path}.{k}", "extra_key", val[k]))
    elif isinstance(tmpl, list):
        if tmpl and isinstance(tmpl[0], list):            # multi-label enum
            vals = val if isinstance(val, list) else [val]
            for v in vals:
                out.append((path, "multienum" if v in tmpl[0] else "bad_enum", v))
        elif tmpl and isinstance(tmpl[0], (dict, str)) and len(tmpl) == 1 and (isinstance(tmpl[0], dict) or tmpl[0] in ("verbatim-string", "string")):
            vals = val if isinstance(val, list) else [val]
            for i, v in enumerate(vals):
                _walk(tmpl[0], v, f"{path}[{i}]", out)
        else:                                               # single enum
            if isinstance(val, list) and len(val) == 1:
                val = val[0]
            out.append((path, "enum" if val in tmpl else "bad_enum", val))
    elif tmpl == "verbatim-string":
        out.append((path, "verbatim", val))
    elif tmpl == "string":
        out.append((path, "string", val))
    elif tmpl == "integer":
        out.append((path, "integer" if isinstance(val, int) or (isinstance(val, str) and val.isdigit()) else "bad_int", val))


def check(obj, passage, template=None):
    """Return dict of counts and the list of ungrounded verbatim values."""
    psq = squash(passage)
    leaves = []
    _walk(template or TEMPLATE, obj or {}, "", leaves)
    stats = {"verbatim": 0, "grounded": 0, "bad_enum": 0, "extra_key": 0, "type_error": 0, "bad_int": 0}
    ungrounded = []
    for path, kind, v in leaves:
        if kind == "verbatim":
            if not isinstance(v, str):
                stats["type_error"] += 1; continue
            stats["verbatim"] += 1
            if grounded(v, psq):
                stats["grounded"] += 1
            else:
                ungrounded.append((path, v))
        elif kind in stats:
            stats[kind] += 1
    stats["n_tasks"] = len((obj or {}).get("tasks") or [])
    return stats, ungrounded


def clean(obj, passage):
    """Drop ungrounded verbatim values and invalid enums (set to None); returns a new object."""
    psq = squash(passage)

    def rec(t, v):
        if v is None:
            return None
        if isinstance(t, dict):
            if not isinstance(v, dict):
                return None
            return {k: rec(tt, v.get(k)) for k, tt in t.items()}
        if isinstance(t, list):
            if t and isinstance(t[0], list):
                vs = v if isinstance(v, list) else [v]
                vs = [x for x in vs if x in t[0]]
                return vs or None
            if len(t) == 1 and (isinstance(t[0], dict) or t[0] in ("verbatim-string", "string")):
                vs = v if isinstance(v, list) else [v]
                out = [rec(t[0], x) for x in vs]
                out = [x for x in out if x not in (None, {}, "") and not (isinstance(x, dict) and all(y is None for y in x.values()))]
                return out or ([] if isinstance(t[0], dict) else None)
            if isinstance(v, list) and len(v) == 1:
                v = v[0]
            return v if isinstance(v, str) and v in t else None
        if t == "verbatim-string":
            return v if isinstance(v, str) and grounded(v, psq) else None
        if t == "string":
            return v if isinstance(v, str) and v.strip() else None
        if t == "integer":
            try:
                return int(v)
            except Exception:
                return None
        return v
    return rec(TEMPLATE, obj or {"tasks": []})
