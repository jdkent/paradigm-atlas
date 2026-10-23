"""Sectionize paper text and select the passages that describe tasks.

Zone patterns are copied from pondie/extraction/prompt/preprocess.py (STRONG/WEAK tiers; a subsection inherits
its parent's zone unless its own heading names one). This version keeps character offsets, which span
grounding needs. It also accepts bare (non-markdown) headings, so ACE/PDF text works.
"""
import re
from dataclasses import dataclass

_MD_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$", re.M)
# bare heading: short line, Title-ish, no terminal period, followed by a line of prose
_BARE_HEADING = re.compile(r"^(?:\d+(?:\.\d+)*\.?\s+)?([A-Z][^\n.!?]{2,80})$", re.M)

_STRONG = [
    ("back", re.compile(r"\b(reference|bibliograph|acknowledg|conflict|competing interest|funding|author contribution|"
                        r"data availability|supplement|appendix|abbreviation|disclosure|declaration|footnote|highlight)", re.I)),
    ("tables", re.compile(r"^tables?\b", re.I)),
    ("front", re.compile(r"^\s*abstract\b|:\s*$", re.I)),
    ("results", re.compile(r"\b(results?|findings?)\b", re.I)),
    ("discussion", re.compile(r"\b(discussion|conclusions?|limitations?|implications?|interpretation)\b", re.I)),
    ("intro", re.compile(r"\b(introduction|background|rationale)\b", re.I)),
    ("methods", re.compile(r"\b(methods?|materials?|procedures?|participants?|subjects?|sample|cohort|acquisitions?|"
                           r"apparatus|preprocess\w*|pre-process\w*|ethics?|recruit\w*)\b", re.I)),
]
_WEAK = [("methods", re.compile(r"\b(analys[ei]s|modell?ing|statistic\w*|design|tasks?|stimul\w*|measures?|mask\w*|roi|"
                                r"segmentation|normali[sz]ation|pipeline|experiment\w*|questionnaire|assessment|drug|dose|"
                                r"administration|scann?\w*|imaging|connectivity|paradigm|conditions?)\b", re.I))]

# Task relevance of a heading (within methods). Positive and negative cues.
TASK_POS = re.compile(r"\b(tasks?|paradigms?|stimul\w*|procedures?|experiment\w*|design|trials?|conditions?|behavio\w*|"
                      r"materials?|apparatus|instructions?|games?|training|protocol|session|run|localizer|"
                      r"go/no-?go|n-?back|stroop|flanker|oddball|memory|learning|reward|emotion|naming|reading|"
                      r"listening|viewing|rest(?:ing)?)\b", re.I)
TASK_NEG = re.compile(r"\b(participants?|subjects?|sample|recruit\w*|ethic\w*|acquisition|scann(?:ing|er) parameters|"
                      r"preprocess\w*|pre-process\w*|statistic\w*|analys[ei]s|first[- ]level|second[- ]level|"
                      r"image processing|data processing|connectivity analysis|segmentation|registration|"
                      r"genotyp\w*|blood|demographic\w*|inclusion|exclusion|clinical (?:assessment|measures)|"
                      r"mri data|imaging parameters|structural|diffusion)\b", re.I)
PARA_CUES = re.compile(r"\b(eyes (?:open|closed)|keep (?:their|the) eyes|resting[- ]state|rest(?:ed)? quietly|"
                       r"(?:were|was) (?:asked|instructed) to|task|paradigm|stimul(?:i|us)|trials?|blocks?|condition|"
                       r"fixation|cross-?hair|responded|button|participants (?:viewed|saw|heard|performed|completed))", re.I)
BODY_CUES = re.compile(r"\b(participants? (?:were|was) (?:asked|instructed|presented|shown|required)|"
                       r"press(?:ed)? (?:a|the|one of)\b|button|each trial|trials?\b|blocks? of|stimuli|"
                       r"fixation cross|presented for|inter-?stimulus|response box|E-?Prime|Presentation|PsychoPy|"
                       r"Psychtoolbox|instructed to|were told)", re.I)


@dataclass
class Section:
    level: int
    heading: str
    start: int   # offset of heading line (or body start for front matter)
    body_start: int
    end: int
    zone: str

    def text(self, doc):
        return doc[self.start:self.end]


def _classify(h):
    for z, p in _STRONG:
        if p.search(h):
            return z, "strong"
    for z, p in _WEAK:
        if p.search(h):
            return z, "weak"
    return "other", "none"


def _marks(text):
    md = [(len(m.group(1)), m.group(2), m.start(), m.end()) for m in _MD_HEADING.finditer(text)]
    if len(md) >= 3:
        return md
    out = []  # bare headings: line followed by blank or longer prose line
    for m in _BARE_HEADING.finditer(text):
        line = m.group(0)
        if len(line.split()) > 12 or line.endswith((",", ";", ":")):
            continue
        nxt = text[m.end():m.end() + 300].lstrip("\n")
        if len(nxt.split("\n", 1)[0]) < 60:
            continue
        lvl = 3 if re.match(r"^\d+\.\d+", line) else 2
        out.append((lvl, m.group(1).strip(), m.start(), m.end()))
    return out


def split_sections(text):
    marks = _marks(text)
    secs = []
    if not marks or marks[0][2] > 0:
        secs.append(Section(0, "front", 0, 0, marks[0][2] if marks else len(text), "front"))
    stack = []
    for i, (level, heading, s, e) in enumerate(marks):
        end = marks[i + 1][2] if i + 1 < len(marks) else len(text)
        while stack and stack[-1][0] >= level:
            stack.pop()
        zone, strength = _classify(heading)
        if i == 0 and s < 5:            # title line at offset 0
            zone, strength = "front", "strong"
        if re.search(r"highlight|graphical abstract|keywords", heading, re.I):
            zone, strength = "front", "strong"
        parent = stack[-1][1] if stack else "other"
        if parent in ("front", "back"):  # front/back matter never parents body sections
            parent = "other"
        if (strength != "strong" and parent != "other") or strength == "none":
            zone = parent if parent != "other" else zone
        stack.append((level, zone))
        secs.append(Section(level, heading, s, e, end, zone))
    return secs


def task_score(sec, text):
    h = sec.heading
    body = text[sec.body_start:sec.end]
    pos = len(TASK_POS.findall(h)); neg = len(TASK_NEG.findall(h))
    cues = len(BODY_CUES.findall(body))
    density = cues / max(1, len(body) / 1000)
    return 2.0 * pos - 2.5 * neg + min(density, 4.0)


def select_task_passages(text, budget_chars=14000, min_score=1.0, include_front=True):
    """Return list of (start, end) spans to show the extractor, in document order.

    Methods-zone sections with task_score >= min_score, plus the abstract (front) truncated to 1500 chars.
    If nothing qualifies (no headings / odd layout), fall back to the highest-cue windows anywhere outside back matter.
    """
    secs = split_sections(text)
    chosen = []
    for s in secs:
        if s.zone == "methods" and s.end - s.body_start > 80:
            sc = task_score(s, text)
            if sc >= min_score:
                chosen.append((sc, s))
    spans = []
    if include_front and secs:
        body0 = next((x.start for x in secs if x.zone in ("intro", "methods", "results", "discussion")
                      and x.start > 0), len(text))
        spans.append((0, min(body0, 1800)))
    used = sum(e - s for s, e in spans)
    for sc, s in sorted(chosen, key=lambda x: -x[0]):
        L = s.end - s.start
        if used + L > budget_chars:
            if used + 1500 < budget_chars:
                spans.append((s.start, s.start + budget_chars - used)); used = budget_chars
            continue
        spans.append((s.start, s.end)); used += L
    # paragraph pass: rescue cue-bearing paragraphs from methods sections not chosen (e.g. rest instructions in
    # 'MRI acquisition'), and from results/front 'experiment' paragraphs that name tasks.
    chosen_ids = {id(s) for _, s in chosen}
    paras = []
    for s in secs:
        if s.zone not in ("methods", "other") or id(s) in chosen_ids:
            continue
        for m in re.finditer(r"[^\n]+", text[s.body_start:s.end]):
            c = len(PARA_CUES.findall(m.group(0)))
            if c >= 2 and len(m.group(0)) > 60:
                a = s.body_start + m.start()
                paras.append((c, a, a + len(m.group(0))))
    for c, a, b in sorted(paras, reverse=True):
        if used + (b - a) > budget_chars:
            continue
        spans.append((a, b)); used += b - a
    if len(spans) <= 1:  # fallback: sliding windows by body-cue density
        W = 3000
        wins = []
        for i in range(0, max(1, len(text) - W), W // 2):
            seg = text[i:i + W]
            if re.search(r"\n#+\s*references", seg, re.I):
                break
            wins.append((len(BODY_CUES.findall(seg)), i))
        for c, i in sorted(wins, reverse=True):
            if used + W > budget_chars or c == 0:
                break
            spans.append((i, min(len(text), i + W))); used += W
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(e, merged[-1][1]))
        else:
            merged.append((s, e))
    return merged


def render(text, spans):
    """Concatenate spans with an elision marker; returns (rendered, offset_map) where offset_map lists
    (rendered_start, source_start, length) so verbatim values can be mapped back to source offsets."""
    out, omap, pos = [], [], 0
    for i, (s, e) in enumerate(spans):
        if i:
            out.append("\n[...]\n"); pos += 7
        omap.append((pos, s, e - s)); out.append(text[s:e]); pos += e - s
    return "".join(out), omap
