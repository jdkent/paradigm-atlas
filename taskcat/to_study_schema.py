"""Emit study_schema-shaped records (neuroimaging-study-storage/task.yaml @74da550 + branch slots) from TaskMentions.

Implements the 'same' and 'derivable' rows of schema/study_schema_crosswalk.md. Divergent fields (D1-D14) are kept
under `_taskcat` so nothing is lost and the gap stays visible.
"""

_RESP = {
    ("hand_finger", "button_press"): "button_press", ("hand_finger", "keyboard"): "button_press",
    ("hand_finger", "mouse_or_touch"): "button_press", ("hand_finger", "joystick"): "button_press",
    ("hand_finger", "rating_scale"): "button_press",
    ("hand_finger", "movement"): "hand_movement", ("hand_finger", "grip_force"): "hand_movement",
    ("hand_finger", "writing_drawing"): "hand_movement", ("whole_body", "movement"): "hand_movement",
    ("vocal", "speech"): "speech", ("eye", "saccade"): "eye_movement", ("eye", "eye_fixation"): "eye_movement",
}
_COND = {"task": "task_state", "control": "control_state", "baseline": "control_state", "rest": "rest",
         "fixation": "fixation", "task_state": "task_state", "control_state": "control_state"}
_STIM_MOD_SS = {"visual", "auditory", "tactile", "olfactory", "gustatory", "interoceptive"}
_ASSESSMENT_KINDS = {"questionnaire_or_scale", "neuropsychological_test"}


def response_modality(r):
    e, k = r.get("effector"), r.get("kind")
    if (e, k) in _RESP:
        return _RESP[(e, k)]
    if e == "foot":
        return "foot_or_leg_movement"
    if e == "face" or (e == "vocal" and k != "speech"):
        return "oral_nonspeech"
    if e == "none_covert" or k == "no_response":
        return "covert_response"
    return k or e


def to_task(m, resolved_refs=None, card=None):
    """One TaskMention (v0.1/v0.2 dict) -> (kind, record) where kind is 'Task' or 'Assessment'."""
    stim = m.get("stimuli") or []
    mods = sorted({s["modality"] for s in stim if s.get("modality")})
    rec = {
        "name": m.get("name"),
        "description": m.get("description"),
        "conditions": [{"name": c.get("name"), "condition_kind": _COND.get(c.get("kind"), c.get("kind"))}
                       for c in m.get("conditions") or [] if c.get("name")],
        "design_type": (m.get("design") or {}).get("type") if (m.get("design") or {}).get("type") != "unknown" else None,
        "presentation_software": m.get("software"),
        "instructions": m.get("instructions"),
        "references": [c.get("marker") for c in m.get("citations") or [] if c.get("marker")],
        "stimuli": "; ".join(s["content"] for s in stim if s.get("content")) or None,
        "stimulus_modality": [x if x in _STIM_MOD_SS else x for x in mods] or None,
        "response_modality": sorted({response_modality(r) for r in m.get("response") or []} - {None}) or None,
        "performance_measures": m.get("measures"),
        # branch slots (origin/claude/gallant-shannon-dhsj8u)
        "paradigm": m.get("paradigm_term"),
        "reference_ids": [r for r in (resolved_refs or [])] or None,
        "paradigm_category": (card or {}).get("canonical_task"),
    }
    rec["_taskcat"] = {k: m.get(k) for k in ("entity_kind", "setting", "judgment", "feedback", "modification")}
    rec["_taskcat"]["stimuli"] = stim
    rec["_taskcat"]["response"] = m.get("response")
    rec["_taskcat"]["manipulated_factors"] = m.get("manipulated_factors")
    rec["_taskcat"]["design"] = m.get("design")
    rec["_taskcat"]["citation_roles"] = [(c.get("marker"), c.get("role")) for c in m.get("citations") or []]
    kind = "Assessment" if m.get("entity_kind") in _ASSESSMENT_KINDS and m.get("setting") != "during_imaging" else "Task"
    return kind, rec
