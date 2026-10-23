"""Sentence-indexed extraction schema (v0.4) for LLM labeling with strict structured output.

The passage is shown with numbered sentences ([1] ..., [2] ...). Instead of copying verbatim strings:
  - evidence fields (instructions, modification, timing values, n_trials) are lists of sentence indices; their text
    is recovered from the passage, so they are grounded by construction;
  - label fields (name, paradigm_term, stimulus content/set, condition names, factor levels, measures, software,
    citation markers) are {text, sentence}: the short value plus the sentence it comes from. Grounding = the text
    occurs in that sentence (or an adjacent one).
Citation `role` is a set (array of distinct roles): more than one when a citation does several jobs.
`to_mention()` converts back to the v0.2 TaskMention dict used downstream, with char-offset evidence.
"""
import json, re
from .template import (ENTITY_KIND, SETTING, JUDGMENT, MODALITY, STIM_ROLE, EFFECTOR, RESP_KIND, COND_KIND_V2,
                       DESIGN, YN, FEEDBACK, CIT_ROLE, GUIDE)
from .validate import squash
from rapidfuzz import fuzz
SNAP = 88

_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[\"'(\[]?[A-Z0-9])")
_NUL = lambda t: {"anyOf": [t, {"type": "null"}]}
_STR, _INT = {"type": "string"}, {"type": "integer"}


def _balance(t):
    """Trim a snapped span so brackets balance: 'Self-Assessment Manikin ( SAM' -> 'Self-Assessment Manikin ( SAM )'
    is not in the source, so drop the dangling '( ...' tail instead."""
    for o, c in (("(", ")"), ("[", "]")):
        while t.count(o) > t.count(c):
            t = t[:t.rfind(o)].rstrip(" ,;")
        while t.count(c) > t.count(o):
            t = t[t.find(c) + 1:].lstrip(" ,;") if t.find(c) < len(t) / 2 else t[:t.rfind(c)].rstrip(" ,;")
    return t


import threading
_TLS = threading.local()   # pySBD Segmenter keeps per-call state and is NOT thread-safe: one instance per thread


def _segment(line):
    """Sentence spans [(start, end)] within one line, using pySBD (rule-based pragmatic segmenter: handles
    et al., Fig., e.g., vs., decimals). Chosen over spaCy en_core_web_sm and the old regex by
    scripts/compare_sentence_splitters.py (abbreviation mis-splits: pySBD 68, spaCy 172, regex 644 on 200 passages)."""
    seg = getattr(_TLS, "seg", None)
    if seg is None:
        import warnings, pysbd
        warnings.filterwarnings("ignore", category=SyntaxWarning)
        seg = _TLS.seg = pysbd.Segmenter(language="en", clean=False, char_span=True)
    spans, off = [], 0
    try:
        for x in seg.segment(line):
            t = x.sent.strip()
            if not t:
                continue
            i = line.find(t, off)
            if i < 0:                                   # never trust a span we cannot locate exactly
                raise ValueError("span not found")
            spans.append((i, i + len(t))); off = i + len(t)
    except Exception:                                   # fall back to the regex splitter for this line
        spans, off = [], 0
        for part in _SPLIT.split(line):
            i = line.find(part, off)
            if i >= 0 and part.strip():
                spans.append((i, i + len(part))); off = i + len(part)
    # merge after non-terminal abbreviations pySBD still breaks on ("approx. 2.5 s", "ca. 30", "cf. Exp. 1")
    merged = []
    for a, b in spans:
        if merged and _NONTERM.search(line[merged[-1][0]:merged[-1][1]]):
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


_NONTERM = re.compile(r"\b(approx|ca|cf|vs|e\.g|i\.e|Fig|Figs|Eq|Exp|Expt|No|resp|et al|Ref|Refs|Suppl|Tab|Vol|pp|Ch|Sect)\.$")


_BLOCK_BREAK = re.compile(r"^\s*(#{1,6}\s|\[\.\.\.\]\s*$|$)")


def _blocks(passage):
    """Paragraph blocks as (start, end): blank lines, markdown headings and '[...]' gap markers are boundaries;
    single hard line breaks inside a paragraph (PDF/HTML text wrapping) are NOT."""
    blocks, pos, cur = [], 0, None
    for line in passage.split("\n"):
        a, b = pos, pos + len(line)
        if _BLOCK_BREAK.match(line):
            if cur: blocks.append(cur); cur = None
            if line.strip(): blocks.append((a, b))          # heading / gap marker = its own block
        else:
            cur = (cur[0], b) if cur else (a, b)
        pos = b + 1
    if cur: blocks.append(cur)
    return blocks


_B36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def sid(n):
    """Non-sequential 3-character sentence ID for position n (bijection on 0..46655: n*7919 mod 36^3), so the
    model must COPY the tag; with sequential numbers a reasoning model counted sentences and drifted."""
    v = (n * 7919) % 46656
    return _B36[v // 1296] + _B36[(v // 36) % 36] + _B36[v % 36]


_SID_INV = {sid(n): n for n in range(1, 46656)}


def sid_to_index(x):
    """Sentence ID (or int / numeric string, for older outputs) -> 1-based index or None."""
    if isinstance(x, int):
        return x
    if isinstance(x, str):
        x = x.strip().strip("[]").lower()
        return _SID_INV.get(x) or (int(x[1:]) if x[:1] == "s" and x[1:].isdigit() else None)
    return None


def number_sentences(passage, tag=None):
    """tag: format string, default '[S{n}]' (pondie's convention). Non-sequential IDs (sid) were tried and are not
    needed: the apparent 'counting drift' was a pySBD thread-safety bug, fixed with a thread-local segmenter."""
    """-> (numbered_text, sentences[(start, end)]). Paragraphs are reflowed (newline -> space, same length, so
    offsets into `passage` are unchanged) and segmented with pySBD; headings and '[...]' get their own number."""
    sents, out = [], []
    for a, b in _blocks(passage):
        block = passage[a:b].replace("\n", " ")
        for x, y in _segment(block):
            sents.append((a + x, a + y))
            out.append((tag or "[S{n}]").format(n=len(sents)) + " " + block[x:y])
    return "\n".join(out), sents


def _obj(props):
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def _enum(v): return _NUL({"enum": v})
def _set(v): return {"type": "array", "items": {"enum": v}}
_LABEL = _NUL(_obj({"text": _STR, "sentence": _INT}))          # short value + the [S#] number of its sentence
_LABELS = {"type": "array", "items": _obj({"text": _STR, "sentence": _INT})}
_SENTS = {"type": "array", "items": _INT}                       # evidence by [S#] number only

TASK = _obj({
    "name": _LABEL, "paradigm_term": _LABEL,
    "entity_kind": _enum(ENTITY_KIND), "setting": _enum(SETTING),
    "description": _NUL(_STR),
    "instructions_sentences": _SENTS,
    "judgment": _set(JUDGMENT),
    "stimuli": {"type": "array", "items": _obj({"content": _LABEL, "modality": _enum(MODALITY), "stimulus_set": _LABEL,
                                                "role": _enum(STIM_ROLE)})},
    "response": {"type": "array", "items": _obj({"effector": _enum(EFFECTOR), "kind": _enum(RESP_KIND),
                                                 "n_alternatives": _NUL(_INT), "speeded": _enum(YN)})},
    "conditions": {"type": "array", "items": _obj({"name": _LABEL, "kind": _enum(COND_KIND_V2)})},
    "manipulated_factors": {"type": "array", "items": _obj({"factor": _NUL(_STR), "levels": _LABELS})},
    "design": _obj({"type": _enum(DESIGN), "n_runs": _NUL(_INT), "n_trials_sentences": _SENTS,
                    "timing_sentences": _SENTS, "adaptive": _enum(YN)}),
    "feedback": _set(FEEDBACK),
    "measures": _LABELS, "software": _LABEL,
    "citations": {"type": "array", "items": _obj({"marker": _LABEL, "roles": _set(CIT_ROLE)})},
    "modification_sentences": _SENTS,
})
SCHEMA = _obj({"tasks": {"type": "array", "items": TASK}})

GUIDE_S = GUIDE.split("Return ONE JSON object")[0] + """The excerpt is split into sentences, each prefixed by a tag such as [S12]. Use the number in the tag of the sentence
that states the value (copy it from the tag; do not count sentences).
Return ONE JSON object matching the response schema (it is enforced). Conventions:
- Fields shaped {text, sentence}: `text` is the short value exactly as written in the excerpt (trimmed to the value
  itself) and `sentence` is the number in the [S#] tag of the sentence it comes from. Use null when not stated.
- Fields ending in `_sentences`: the [S#] numbers of the sentences that state it (no text). Empty list if not stated.
- Single-choice fields take exactly one option or null; set-valued fields take zero or more distinct options.
""" + "\n" + GUIDE[GUIDE.index("What counts as a task"):GUIDE.index("Field guidance:")] + """
Field guidance:
- name {text, sentence}: the paper's own name for the task (e.g. "emotional reactivity task"); if never named, the
  shortest phrase that refers to it (e.g. "the resting-state scan").
- paradigm_term {text, sentence}: ONLY if the excerpt itself uses an established paradigm term for this task
  ("n-back", "go/no-go", "Stroop", "monetary incentive delay", "dot-probe", "oddball"). Never inferred.
- description: 1-3 sentences in your words: what was presented and what participants had to do.
- instructions_sentences: sentences stating the instruction or response rule.
- judgment: the mental operation(s) asked of participants per trial (set).
- stimuli: each distinct stimulus class; content {text, sentence} (e.g. "fearful and neutral faces"); stimulus_set
  only for a named database/set (e.g. "IAPS", "NimStim").
- response: effector and kind; n_alternatives if stated or obvious; speeded = yes if instructed to respond fast.
- conditions: conditions/trial types/blocks as named ({text, sentence}) with their kind (task_state, control_state,
  rest, fixation).
- manipulated_factors: the independent variables (factor in your words; levels {text, sentence}).
- design: type; n_runs; n_trials_sentences and timing_sentences (durations, ISI/ITI) as sentence numbers.
- measures: behavioral outcomes recorded ({text, sentence}, e.g. "reaction times"); software {text, sentence}.
- citations: every citation marker in the sentences describing THIS task (marker {text, sentence}, e.g. "[12]",
  "(Hariri et al., 2002)"), with roles = the SET of roles it plays for this task: task_origin (introduced the task),
  adapted_from (task taken/modified from that paper's version), prior_use (used as in previous studies, often the
  same authors), stimulus_set (source of stimuli), implementation (software/code), analysis_method, dataset,
  background (other). Usually one role; list several only when the citation genuinely does several jobs.
- modification_sentences: sentences stating how the task departs from the cited/standard version.
Use null / empty lists for anything not stated. Output only the JSON.
"""


def messages(title, passage):
    numbered, _ = number_sentences(passage)
    return [{"role": "system", "content": GUIDE_S},
            {"role": "user", "content": f"Paper title: {title}\n\nExcerpt (sentences tagged [S#]):\n<<<\n{numbered}\n>>>"}]


def ground_label(x, passage, sents, stat=None):
    """{text, sentence} -> grounded source text (exact or snapped) or None."""
    stat = stat if stat is not None else {"labels": 0, "grounded": 0}
    if not x or not x.get("text"):
        return None
    stat["labels"] = stat.get("labels", 0) + 1
    i = sid_to_index(x.get("sentence")); txt = x["text"].strip()
    cand = [j for j in (i, (i or 0) - 1, (i or 0) + 1) if isinstance(j, int) and 1 <= j <= len(sents)]
    sq = squash(txt)
    for j in cand:
        if sq and sq in squash(passage[sents[j - 1][0]:sents[j - 1][1]]):
            stat["grounded"] = stat.get("grounded", 0) + 1
            return txt, j
    core = txt.strip("()[] "); best = None
    for j in cand:
        st = passage[sents[j - 1][0]:sents[j - 1][1]]
        al = fuzz.partial_ratio_alignment(core.lower(), st.lower())
        if al and (best is None or al.score > best[0]):
            a, b = al.dest_start, al.dest_end
            while a > 0 and st[a - 1].isalnum() and st[a].isalnum(): a -= 1
            while b < len(st) and b > 0 and st[b - 1].isalnum() and st[b].isalnum(): b += 1
            span = st[a:b]
            if len(span) > len(core) * 1.4:
                span = st[al.dest_start:al.dest_end].rsplit(" ", 1)[0]
            best = (al.score, span, j)
    if not (best and best[0] >= SNAP and len(best[1].strip()) >= 0.6 * len(core)) and sq:
        hits = [k for k, (sa, sb) in enumerate(sents, 1) if sq in squash(passage[sa:sb])]
        if hits:                                       # verbatim elsewhere: keep text, correct the index
            k = min(hits, key=lambda h: abs(h - (i or h)))
            stat["grounded"] = stat.get("grounded", 0) + 1; stat["index_corrected"] = stat.get("index_corrected", 0) + 1
            return txt, k
    if best and best[0] >= SNAP and len(best[1].strip()) >= 0.6 * len(core):
        stat["grounded"] = stat.get("grounded", 0) + 1; stat["snapped"] = stat.get("snapped", 0) + 1
        t = _balance(re.sub(r"[\s,;]+(and|or|but|with|of|the|a|an)$", "", best[1].strip(" ,;"), flags=re.I).strip(" ,;"))
        return (t, best[2]) if t else None
    return None


def clean_for_student(obj, passage):
    """Consensus v0.4 extraction -> student training target: every label replaced by its grounded source text and
    sentence (ungrounded labels -> null / removed), out-of-range sentence indices removed, internal keys dropped."""
    _, sents = number_sentences(passage)
    n = len(sents)
    def L(x):
        g = ground_label(x, passage, sents)
        return {"text": g[0], "sentence": g[1]} if g else None
    def I(ix): return sorted({j for j in (sid_to_index(i) for i in ix or []) if isinstance(j, int) and 1 <= j <= n})
    tasks = []
    for t in (obj or {}).get("tasks") or []:
        name = L(t.get("name"))
        if not name:
            continue                                   # a task without a grounded name is not trainable
        d = t.get("design") or {}
        tasks.append({
            "name": name, "paradigm_term": L(t.get("paradigm_term")), "entity_kind": t.get("entity_kind"),
            "setting": t.get("setting"), "description": t.get("description"),
            "instructions_sentences": I(t.get("instructions_sentences")), "judgment": t.get("judgment") or [],
            "stimuli": [{"content": L(x.get("content")), "modality": x.get("modality"), "stimulus_set": L(x.get("stimulus_set")),
                         "role": x.get("role")} for x in t.get("stimuli") or [] if L(x.get("content"))],
            "response": t.get("response") or [],
            "conditions": [{"name": L(c.get("name")), "kind": c.get("kind")} for c in t.get("conditions") or [] if L(c.get("name"))],
            "manipulated_factors": [{"factor": f.get("factor"), "levels": [v for v in (L(l) for l in f.get("levels") or []) if v]}
                                    for f in t.get("manipulated_factors") or []],
            "design": {"type": d.get("type"), "n_runs": d.get("n_runs"), "n_trials_sentences": I(d.get("n_trials_sentences")),
                       "timing_sentences": I(d.get("timing_sentences")), "adaptive": d.get("adaptive")},
            "feedback": t.get("feedback") or [], "measures": [v for v in (L(m) for m in t.get("measures") or []) if v],
            "software": L(t.get("software")),
            "citations": [{"marker": L(c.get("marker")), "roles": c.get("roles") or []} for c in t.get("citations") or [] if L(c.get("marker"))],
            "modification_sentences": I(t.get("modification_sentences")),
        })
    return {"tasks": tasks}


def to_mention(obj, passage):
    """Sentence-indexed extraction -> v0.2 TaskMention (text values) + evidence spans + grounding report."""
    _, sents = number_sentences(passage)
    stat = {"labels": 0, "grounded": 0, "bad_index": 0}

    def sent_text(ix):
        ix = [sid_to_index(i) for i in ix or []]
        ok = [i for i in ix if isinstance(i, int) and 1 <= i <= len(sents)]
        stat["bad_index"] += len(ix or []) - len(ok)
        return " ".join(passage[sents[i - 1][0]:sents[i - 1][1]] for i in ok) or None, [list(sents[i - 1]) for i in ok]

    def label(x):
        g = ground_label(x, passage, sents, stat)
        return g[0] if g else None

    tasks = []
    for t in (obj or {}).get("tasks") or []:
        d = t.get("design") or {}
        ins, ins_ev = sent_text(t.get("instructions_sentences"))
        mod, _ = sent_text(t.get("modification_sentences"))
        ntr, _ = sent_text(d.get("n_trials_sentences"))
        tim, _ = sent_text(d.get("timing_sentences"))
        tasks.append({
            "name": label(t.get("name")), "paradigm_term": label(t.get("paradigm_term")),
            "entity_kind": t.get("entity_kind"), "setting": t.get("setting"), "description": t.get("description"),
            "instructions": ins, "judgment": t.get("judgment") or None,
            "stimuli": [{"content": label(s.get("content")), "modality": s.get("modality"),
                         "stimulus_set": label(s.get("stimulus_set")), "role": s.get("role")} for s in t.get("stimuli") or []],
            "response": t.get("response") or [],
            "conditions": [{"name": label(c.get("name")), "kind": c.get("kind")} for c in t.get("conditions") or []],
            "manipulated_factors": [{"factor": f.get("factor"), "levels": [v for v in (label(l) for l in f.get("levels") or []) if v]}
                                    for f in t.get("manipulated_factors") or []],
            "design": {"type": d.get("type"), "n_runs": d.get("n_runs"), "n_trials": ntr, "stimulus_duration": None,
                       "trial_duration": None, "isi_iti": None, "total_duration": None, "timing": tim, "adaptive": d.get("adaptive")},
            "feedback": t.get("feedback") or None,
            "measures": [v for v in (label(m) for m in t.get("measures") or []) if v],
            "software": label(t.get("software")),
            "citations": [{"marker": label(c.get("marker")), "roles": sorted(set(c.get("roles") or [])),
                           "role": (sorted(set(c.get("roles") or [])) or [None])[0]} for c in t.get("citations") or []],
            "modification": mod,
            "evidence": {"instructions": ins_ev},
        })
    return {"tasks": tasks}, stat
