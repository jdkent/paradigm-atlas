"""NuExtract3 template for TaskMention extraction (schema/task_schema.yaml layer 1) and the silver-labeler prompt."""
import json

ENTITY_KIND = ["experimental_task", "resting_state", "passive_stimulation", "naturalistic", "localizer",
               "questionnaire_or_scale", "neuropsychological_test", "intervention_or_training"]
SETTING = ["during_imaging", "outside_imaging", "both", "not_imaging"]
JUDGMENT = ["attend", "count", "detect", "discriminate", "categorize", "compare", "match", "identify", "recognize",
            "recall", "encode", "learn", "judge", "rate", "choose", "predict", "plan", "imagine", "generate", "name",
            "read", "repeat", "move", "track", "navigate", "inhibit", "switch", "regulate", "fixate", "rest",
            "passive_view", "passive_listen", "play", "other"]
MODALITY = ["visual", "auditory", "tactile", "olfactory", "gustatory", "interoceptive", "nociceptive", "thermal",
            "vestibular", "electrical", "multimodal"]
STIM_ROLE = ["target", "non_target", "distractor", "cue", "prime", "probe", "sample", "feedback", "reward", "penalty",
             "go_signal", "stop_signal", "context", "other"]
EFFECTOR = ["hand_finger", "foot", "vocal", "eye", "face", "whole_body", "none_covert"]
RESP_KIND = ["button_press", "keyboard", "joystick", "mouse_or_touch", "rating_scale", "speech", "saccade",
             "eye_fixation", "grip_force", "movement", "writing_drawing", "physiological", "no_response"]
COND_KIND = ["task", "control", "rest", "fixation", "baseline"]
DESIGN = ["block", "event_related", "mixed", "continuous", "unknown"]
YN = ["yes", "no", "unknown"]
FEEDBACK = ["none", "performance", "monetary", "points", "social", "aversive", "primary_reward"]
CIT_ROLE = ["task_origin", "adapted_from", "prior_use", "stimulus_set", "implementation", "analysis_method",
            "dataset", "background"]

TEMPLATE = {"tasks": [{
    "name": "verbatim-string",
    "paradigm_term": "verbatim-string",
    "entity_kind": ENTITY_KIND,
    "setting": SETTING,
    "description": "string",
    "instructions": "verbatim-string",
    "judgment": [JUDGMENT],
    "stimuli": [{"content": "verbatim-string", "modality": MODALITY, "stimulus_set": "verbatim-string",
                 "role": STIM_ROLE}],
    "response": [{"effector": EFFECTOR, "kind": RESP_KIND, "n_alternatives": "integer", "speeded": YN}],
    "conditions": [{"name": "verbatim-string", "kind": COND_KIND}],
    "manipulated_factors": [{"factor": "string", "levels": ["verbatim-string"]}],
    "design": {"type": DESIGN, "n_runs": "integer", "n_trials": "verbatim-string",
               "stimulus_duration": "verbatim-string", "trial_duration": "verbatim-string",
               "isi_iti": "verbatim-string", "total_duration": "verbatim-string", "adaptive": YN},
    "feedback": [FEEDBACK],
    "measures": ["verbatim-string"],
    "software": "verbatim-string",
    "citations": [{"marker": "verbatim-string", "role": CIT_ROLE}],
    "modification": "verbatim-string",
}]}
TEMPLATE_STR = json.dumps(TEMPLATE, ensure_ascii=False)

GUIDE = """You extract descriptions of the TASKS that participants performed in a research study, from excerpts of
the paper (the abstract plus selected Methods passages; "[...]" marks omitted text).

Return ONE JSON object that follows the template exactly. Template conventions:
- "verbatim-string": copy an exact substring of the excerpt (same words, same order; you may trim it). Never
  paraphrase, translate, normalize, or compose. If the excerpt does not contain it, use null.
- "string": a short free-text value in your own words.
- a list of options, e.g. ["a","b"]: choose exactly one option, or null.
- a list containing a list of options, e.g. [["a","b"]]: choose zero or more options, as a JSON list.
- "integer": a number, or null.
- a list containing an object: zero or more such objects.

What counts as a task: anything participants did or underwent that is described as part of the study protocol:
experimental tasks in or out of the scanner, resting-state scans, passive stimulation (e.g. pain, tones),
naturalistic viewing/listening (movies, stories), functional localizers, and behavioral/neuropsychological tests or
questionnaires administered as part of the study. Use entity_kind to say which. Do NOT create tasks for imaging
acquisitions, analyses (VBM, DTI, connectivity), or sample characteristics. If the excerpt describes no task,
return {"tasks": []}.
One entry per distinct task. Practice versions, runs, or sessions of the same task are one task. The phases of one
experiment (e.g. study/encoding then test/retrieval of the same material; acquisition then extinction of conditioning;
training then test) are ONE task: name it by the paper's name for the whole experiment and list the phases as
conditions. Two tasks that share a run but differ in procedure are two tasks. A battery of separately scored tests
is one entry per test.

Field guidance:
- name: the paper's own name for the task, verbatim (e.g. "emotional reactivity task"). If the paper never names
  it, copy the shortest phrase that refers to it (e.g. "the resting-state scan").
- paradigm_term: ONLY if the excerpt itself uses an established paradigm term for this task (e.g. "n-back",
  "go/no-go", "Stroop", "monetary incentive delay", "dot-probe", "oddball", "Iowa Gambling Task"), copy it verbatim.
  Do not infer the paradigm from the procedure or from citations. Often this equals or is contained in name.
- description: 1-3 sentences, your words: what was presented and what participants had to do.
- instructions: verbatim instruction or response rule (e.g. "press the left button when the face is female").
- judgment: the mental operation(s) asked of participants per trial.
- stimuli: each distinct stimulus class; content verbatim (e.g. "fearful and neutral faces", "two-syllable words");
  stimulus_set only if a named database/set is given (e.g. "IAPS", "NimStim", "Karolinska Directed Emotional Faces").
- response: how participants responded. n_alternatives = number of response options if stated or obvious.
  speeded = yes if instructed to respond as fast as possible / under deadline.
- conditions: the conditions/trial types/blocks as named in the paper (verbatim), with their kind.
- manipulated_factors: the independent variables (your words for the factor, verbatim levels).
- design: block / event_related / mixed as reported; numbers and timing copied verbatim with units.
- measures: behavioral outcome measures recorded for the task (verbatim: "reaction times", "accuracy").
- citations: every citation marker that appears in the sentences describing THIS task (verbatim marker, e.g.
  "[12]", "(Hariri et al., 2002)", "Kirby et al. (1999)"), with its role:
  task_origin = the paper that introduced the task; adapted_from = task taken/modified from that paper's version;
  prior_use = the task was used as in previous studies (often the same authors); stimulus_set = source of stimuli;
  implementation = software/code; analysis_method; dataset = data/cohort source; background = other.
- modification: verbatim statement of how the task was changed relative to the cited/standard version.
Use null for anything not stated. Output only the JSON."""


def labeler_messages(title, passage, template_str=None):
    # v0.2 template (study_schema ConditionKind) matches the strict schema used in silver_label.py
    user = (f"Template:\n{template_str or TEMPLATE_V2_STR}\n\nPaper title: {title}\n\nExcerpt:\n<<<\n{passage}\n>>>")
    return [{"role": "system", "content": GUIDE}, {"role": "user", "content": user}]


def nuextract_document(title, passage):
    return f"Title: {title}\n\n{passage}"


# v0.2 training template: condition kinds renamed to study_schema ConditionKind (crosswalk D-none: 'same').
COND_KIND_V2 = ["task_state", "control_state", "rest", "fixation"]
_COND_MAP = {"task": "task_state", "control": "control_state", "baseline": "control_state", "rest": "rest",
             "fixation": "fixation"}
TEMPLATE_V2 = json.loads(TEMPLATE_STR)
TEMPLATE_V2["tasks"][0]["conditions"][0]["kind"] = COND_KIND_V2
TEMPLATE_V2_STR = json.dumps(TEMPLATE_V2, ensure_ascii=False)


def to_v2(obj):
    """Map a cleaned v0.1 extraction to v0.2 vocabulary."""
    for t in (obj or {}).get("tasks") or []:
        for c in t.get("conditions") or []:
            if c.get("kind") in _COND_MAP:
                c["kind"] = _COND_MAP[c["kind"]]
        d = t.get("design") or {}
        if d.get("type") == "unknown":
            d["type"] = None
        if d.get("adaptive") == "unknown":
            d["adaptive"] = None
        for r in t.get("response") or []:
            if r.get("speeded") == "unknown":
                r["speeded"] = None
    return obj


# v0.3 two-pass templates: LIST (enumerate tasks, short output) then DETAIL (one task at a time).
TEMPLATE_LIST = {"tasks": [{"name": "verbatim-string", "entity_kind": ENTITY_KIND, "setting": SETTING}]}
TEMPLATE_LIST_STR = json.dumps(TEMPLATE_LIST, ensure_ascii=False)
TEMPLATE_DETAIL = dict(TEMPLATE_V2["tasks"][0])
TEMPLATE_DETAIL_STR = json.dumps(TEMPLATE_DETAIL, ensure_ascii=False)


def detail_document(title, passage, task_name):
    return f"Target task: {task_name}\nTitle: {title}\n\n{passage}"
