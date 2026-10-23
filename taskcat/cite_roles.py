"""Rule cues for citation roles, applied to the sentence that contains a citation marker.

Rules were written from domain knowledge and kept or dropped by their precision against Luna silver roles on the
training papers. The astra gold set is not used to write or select them; it is only the final test.
Roles: task_origin, adapted_from, prior_use, stimulus_set, implementation, analysis_method, dataset, background.
"""
import re
from .validate import squash

# (role, name, pattern) — matched case-insensitively on the citing sentence (marker replaced by [CIT]).
RULES = [
    ("implementation", "software", r"\b(e-?prime|presentation(?: software)?|psychopy|psych(?:ophysics )?toolbox|cogent|inquisit|jspsych|"
                                   r"opensesame|superlab|psyscope|dmdx|eyelink|neurobehavioral systems|psychology software tools)\b"),
    ("implementation", "programmed", r"\b(programm?ed|implemented|coded|run|presented|controlled) (in|using|with|via|through)\b.{0,40}\[CIT\]"),
    ("stimulus_set", "taken_from", r"\b(stimuli|pictures|images|photo(?:graph)?s|faces|words|items|sentences|videos?|clips|scenes|sounds|odou?rs|films?)\b"
                                   r"[^.]{0,60}\b(were |was )?(taken|selected|drawn|chosen|obtained|derived|sampled|adapted|borrowed) from\b"),
    ("stimulus_set", "database", r"\b(database|picture system|stimulus set|face set|image set|norms|normative (data|ratings)|corpus|"
                                 r"affective norms|word list|lexicon|battery of (pictures|images))\b"),
    ("stimulus_set", "named_set", r"\b(iaps|nimstim|kdef|karolinska|ekman|pictures of facial affect|anew|oasis|gaps|radboud|chicago face|"
                                  r"max planck|macbrain|snodgrass|boss|celex|subtlex|mrc psycholinguistic|cafe set)\b"),
    ("analysis_method", "analysis", r"\b(analy[sz]ed|modell?ed|estimated|computed|calculated|fitted|fit|quantified|corrected|scored) "
                                    r"(using|with|as|according to|following|by means of)\b"),
    ("analysis_method", "method_terms", r"\b(drift[- ]diffusion|signal detection|d'|reinforcement learning model|hierarchical bayesian|"
                                        r"general linear model|glm|spm\d*|fsl|afni|freesurfer|ica|dcm|mvpa|integration method|race model)\b"),
    ("dataset", "dataset", r"\b(data|dataset|sample|cohort|participants) (were|was) (drawn|obtained|taken|collected|recruited) (from|as part of)\b|"
                           r"\b(human connectome project|hcp|uk biobank|abcd study|adni|enigma|openneuro|1000 functional)\b"),
    ("adapted_from", "adapted", r"\b(adapted|modified|adopted|derived) (from|after|version)\b|\bmodified version\b|\bvariant of\b|\bversion of\b"
                                r"|\bbased on (the|a|an) .{0,40}(task|paradigm|procedure|design)\b|\bsimilar to (that|the one|those|the task|the paradigm)\b"),
    ("task_origin", "origin", r"\b(originally|first) (developed|described|introduced|proposed|devised|reported)\b|"
                              r"\b(developed|devised|introduced|created|designed) by\b|\boriginal (version|paradigm|task)\b"),
    ("prior_use", "previous", r"\b(as|has been|have been|was) (previously |already )?(described|used|reported|employed|validated|published) "
                              r"(in|by|elsewhere|before)\b|\b(our|we) (previous(ly)?|prior|earlier) (stud|work|report|paper|research)|"
                              r"\bpreviously (validated|used|described|published|employed)\b|\b(used|employed) in (several|many|numerous|"
                              r"previous|prior|earlier|other) (stud|investig|experiment)|\bwidely used\b|\bwell[- ]established\b|"
                              r"\bas in\b.{0,30}\[CIT\]|\bsee\b.{0,20}\[CIT\]"),
]
_COMPILED = [(r, n, re.compile(p, re.I)) for r, n, p in RULES]
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")


def citing_sentence(passage, marker):
    """The sentence of `passage` containing `marker` (whitespace/punctuation-insensitive), marker -> [CIT]."""
    sm = squash(marker or "")
    if not sm:
        return None
    for para in passage.split("\n"):
        for s in _SENT.split(para):
            if sm in squash(s):
                i = s.find(marker)
                return (s[:i] + " [CIT] " + s[i + len(marker):]) if i >= 0 else s + " [CIT]"
    return None


def rule_hits(sentence):
    return [(r, n) for r, n, p in _COMPILED if sentence and p.search(sentence)]


def surname(s):
    s = re.sub(r"[^a-z\- ]", "", (s or "").lower()).strip()
    return s.split()[-1] if s else ""


def apply_rules(model_role, sentence, cited_first_author=None, citing_authors=(), enabled=None, policy="override"):
    """Return (role, reason). policy 'override': a rule hit replaces the model role; 'fill': only when the model
    gave background/None. `enabled` restricts to rule names kept on the dev data."""
    hits = [(r, n) for r, n in rule_hits(sentence) if enabled is None or n in enabled]
    lineage = {"task_origin", "adapted_from", "prior_use"}
    # author overlap: citing your own earlier paper for the task is prior use (or self-adaptation)
    if cited_first_author and citing_authors and (enabled is None or "self_citation" in enabled):
        if surname(cited_first_author) in {surname(a) for a in citing_authors} and model_role in (lineage | {"background", None}):
            if model_role != "adapted_from":
                return "prior_use", "self_citation"
    if not hits:
        return model_role, None
    r, n = hits[0]
    if policy == "fill" and model_role not in ("background", None):
        return model_role, None
    return r, n
