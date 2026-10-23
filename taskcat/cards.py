"""TaskCard assembly: one grounded TaskMention -> one normalized, queryable TaskCard (schema/task_schema.yaml layer 2).

Identity: family -> stem -> canonical task -> variant -> qualifiers (taskcat.decompose)
Routes:   A lexical on paradigm_term / name / description; B procedure classifier (TF-IDF, CPU) on the mention's
          procedure text with task names masked; decided per normalize.combine policy (B decides only >= TB).
Also:     facets (taskcat.facets), conditions (taskcat.conditions, task-context aware), citations resolved to
          refs with role, lineage buckets, authors keyed by ORCID or last+full forename, study_schema record.
"""
import os, pickle, re
from .lexicon import Lexicon, _norm
from .decompose import Decomposer, STEM_OF
from .facets import build_facets
from .conditions import normalize_condition_ctx
from .to_study_schema import to_task
from .citations import resolve_with_bib, resolve

HERE = os.path.dirname(os.path.abspath(__file__))
NON_TASK_KINDS = {"questionnaire_or_scale", "intervention_or_training"}
KIND_DEFAULT = {
    "naturalistic": lambda t: "tct_story_listening" if re.search(r"stor(y|ies)|narrat|listen|audiobook|podcast", t) else "tct_naturalistic_viewing",
    "localizer": lambda t: ("tct_retinotopy" if re.search(r"retinot|wedge|ring|meridian|eccentric", t) else
                            "tct_motion_perception" if re.search(r"\bmt\b|motion", t) else
                            "tct_sound_categorization" if re.search(r"voice|auditory|sound", t) else
                            "tct_motor_execution" if re.search(r"motor|finger|hand", t) else "tct_visual_localizer"),
}


def person_key(a):
    if a.get("orcid"):
        return "orcid:" + re.sub(r".*/", "", a["orcid"])
    last = re.sub(r"[^a-z]", "", (a.get("last") or "").lower())
    fore = re.sub(r"[^a-z]", "", (a.get("fore") or "").lower())
    return f"{last}_{fore}" if last else None


class CardBuilder:
    def __init__(self, TB=0.6):
        self.L = Lexicon(); self.D = Decomposer(self.L); self.TB = TB
        p = os.path.join(HERE, "..", "data", "routeB_tfidf.pkl")
        self.B = pickle.load(open(p, "rb")) if os.path.exists(p) else None
        mp = os.path.join(HERE, "..", "data", "ref_pmid_map.json")
        self.refmap = __import__("json").load(open(mp)) if os.path.exists(mp) else {}
        self._mask = re.compile("|".join(sorted({pt.pattern for pt, _, _ in self.L.patterns}, key=len, reverse=True)), re.I)

    def fam(self, k):
        return (self.L.family.get(k) or [None])[0] if k else None

    def procedure_text(self, t):
        parts = [t.get("description") or "", t.get("instructions") or "",
                 "Stimuli: " + "; ".join(s.get("content") or "" for s in t.get("stimuli") or []),
                 "Conditions: " + "; ".join(c.get("name") or "" for c in t.get("conditions") or [])]
        txt = " ".join(parts)
        for v in {t.get("name") or "", t.get("paradigm_term") or ""}:
            if len(v) > 3:
                txt = re.sub(re.escape(v), "[TASK]", txt, flags=re.I)
        return self._mask.sub("[TASK]", txt)

    def route_b(self, t):
        if not self.B:
            return None
        vec, clf = self.B
        pr = clf.predict_proba(vec.transform([self.procedure_text(t)]))[0]
        i = pr.argmax()
        return clf.classes_[i], float(pr[i])

    def identity(self, t):
        kind = t.get("entity_kind")
        A, src = None, None
        for s, txt in (("paradigm_term", t.get("paradigm_term")), ("name", t.get("name"))):
            m = self.L.match(txt)
            if m:
                A, src = m, s; break
        B = self.route_b(t) if kind not in NON_TASK_KINDS else None
        if kind in NON_TASK_KINDS:
            return None, "gate", [], B
        if kind == "resting_state":
            return "hedtsk_rest", "kind", ["kind"], B
        if A:
            lab, route = A[0], f"A:{src}"
        elif B and B[1] >= self.TB:
            lab, route = B[0], "B"
        else:
            # a paradigm word in the description is weak evidence (descriptions cite other paradigms):
            # accept it only when route B is absent, agrees on family, or is unsure itself
            m = self.L.match(t.get("description"))
            if m and (not B or self.fam(B[0]) == self.fam(m[0]) or B[1] < 0.3):
                lab, route = m[0], "A:description"
            elif B and B[1] >= 0.4:
                lab, route = B[0], "B-low"
            else:
                lab, route = None, None
        if not lab and kind in KIND_DEFAULT:       # entity kind implies a generic paradigm
            txt = f"{t.get('name') or ''} {t.get('description') or ''}".lower()
            lab = KIND_DEFAULT[kind](txt); route = "kind" if lab else None
        agree = [r for r, v in (("A", A[0] if A else None), ("B", B[0] if B else None)) if v and v == lab]
        return lab, route, agree, B

    def build(self, t, paper, bib=None, epmc=None, authors=None):
        lab, route, agree, B = self.identity(t)
        dec = self.D(t.get("name"), t.get("paradigm_term"))
        if lab and dec.get("canonical_task") == "hedtsk_emotional_stroop" and lab == "hedtsk_stroop_color_word":
            lab = "hedtsk_emotional_stroop"
        fam = self.fam(lab)
        conds = [normalize_condition_ctx(c.get("name"), lab, fam) | {"extracted_kind": c.get("kind")}
                 for c in t.get("conditions") or [] if c.get("name")]
        cits = []
        for c in t.get("citations") or []:
            mk = c.get("marker"); role = c.get("role")
            role = (role[0] if role else None) if isinstance(role, list) else role
            if not mk:
                continue
            got = resolve_with_bib(mk, bib) if bib else (resolve(mk, epmc) if epmc else [])
            if not got:
                cits.append({"marker": mk, "role": role, "resolved": False}); continue
            for g in got[:6]:
                pm = g.get("pmid") or g.get("id")
                if not pm:
                    pm = self.refmap.get((g.get("doi") or "").lower() or "t:" + (g.get("title") or "")[:120].lower())
                cits.append({"marker": mk, "role": role, "resolved": True, "pmid": pm,
                             "doi": g.get("doi"), "first_author": g.get("first_author") or (g.get("authorString") or "").split(" ")[0],
                             "year": g.get("year") or g.get("pubYear"), "title": (g.get("title") or "")[:200]})
        def refs(roles):
            return sorted({c["pmid"] for c in cits if c.get("pmid") and c["role"] in roles})
        auth = [{"key": person_key(a), "last": a.get("last"), "fore": a.get("fore"), "orcid": a.get("orcid"),
                 "affiliation": (a.get("affiliations") or [None])[0]} for a in authors or []]
        kind, ss = to_task(t, [c["pmid"] for c in cits if c.get("pmid")], {"canonical_task": STEM_OF.get(lab, lab) if lab else None})
        return {
            **paper, "authors": auth, "senior_author": auth[-1]["key"] if auth else None,
            "name": t.get("name"), "paradigm_term": t.get("paradigm_term"), "entity_kind": t.get("entity_kind"),
            "setting": t.get("setting"), "description": t.get("description"),
            "identity": {"family": fam, "stem": STEM_OF.get(lab, lab) if lab else None, "canonical_task": lab,
                         "canonical_name": self.L.names.get(lab) if lab else None,
                         "variant": dec.get("variant") if dec.get("canonical_task") == lab else None,
                         "qualifiers": dec["qualifiers"], "route": route, "agree": agree,
                         "route_b": list(B) if B else None},
            "facets": build_facets(t), "conditions": conds,
            "citations": cits,
            "lineage": {"origin_refs": refs({"task_origin", "adapted_from"}), "prior_use_refs": refs({"prior_use"}),
                        "stimulus_set_refs": refs({"stimulus_set"})},
            "modification": t.get("modification"),
            "study_schema": {"kind": kind, "record": ss}, "mention": t,
        }
