"""NuExtract3 student templates for the sentence-indexed format (v0.4): numbered passage in, labels as
{text, sentence}, evidence as sentence-index lists, citation roles as a multi-select set. Two-pass LIST + DETAIL."""
import json
from .template import (ENTITY_KIND, SETTING, JUDGMENT, MODALITY, STIM_ROLE, EFFECTOR, RESP_KIND, COND_KIND_V2,
                       DESIGN, YN, FEEDBACK, CIT_ROLE)
from .sentence_schema import number_sentences
LABEL = {"text": "verbatim-string", "sentence": "integer"}
DETAIL = {
    "name": LABEL, "paradigm_term": LABEL, "entity_kind": ENTITY_KIND, "setting": SETTING, "description": "string",
    "instructions_sentences": ["integer"], "judgment": [JUDGMENT],
    "stimuli": [{"content": LABEL, "modality": MODALITY, "stimulus_set": LABEL, "role": STIM_ROLE}],
    "response": [{"effector": EFFECTOR, "kind": RESP_KIND, "n_alternatives": "integer", "speeded": YN}],
    "conditions": [{"name": LABEL, "kind": COND_KIND_V2}],
    "manipulated_factors": [{"factor": "string", "levels": [LABEL]}],
    "design": {"type": DESIGN, "n_runs": "integer", "n_trials_sentences": ["integer"], "timing_sentences": ["integer"], "adaptive": YN},
    "feedback": [FEEDBACK], "measures": [LABEL], "software": LABEL,
    "citations": [{"marker": LABEL, "roles": [CIT_ROLE]}],
    "modification_sentences": ["integer"],
}
LIST = {"tasks": [{"name": LABEL, "entity_kind": ENTITY_KIND, "setting": SETTING}]}
DETAIL_STR = json.dumps(DETAIL, ensure_ascii=False); LIST_STR = json.dumps(LIST, ensure_ascii=False)


def document(title, passage):
    return f"Title: {title}\n\n" + number_sentences(passage)[0]


def detail_document(title, passage, name_label):
    return f"Target task: {name_label['text']} (sentence {name_label['sentence']})\n" + document(title, passage)


def rows_for(dbid, title, passage, target):
    """target = clean_for_student(consensus) -> list of (kind, prompt, template, target_json) rows."""
    tasks = target.get("tasks") or []
    rows = [("list", document(title, passage), LIST_STR,
             json.dumps({"tasks": [{"name": t["name"], "entity_kind": t["entity_kind"], "setting": t["setting"]} for t in tasks]}, ensure_ascii=False))]
    for t in tasks:
        rows.append(("detail", detail_document(title, passage, t["name"]), DETAIL_STR, json.dumps(t, ensure_ascii=False)))
    return rows
