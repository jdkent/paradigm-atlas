"""Layer-2 facet normalization: verbatim TaskMention values -> controlled, queryable facet values.

Vocabularies: stimulus_kind extends hed-task facet_defs.tsv stimulus_kind (CogPO/BrainMap-derived); affect/social
are BrainMap 'Stimulus Content'-like; measures and manipulation axes are corpus-derived keyword maps.
Every facet value keeps the verbatim source string it came from (provenance).
"""
import re

STIMULUS_KIND = [  # (value, pattern) — first match wins per stimulus; order specific -> general
    ("faces", r"\bfac(e|es|ial)\b|expression|ekman|nimstim|kdef|karolinska"),
    ("eyes_gaze", r"\beyes?\b|gaze|eye[- ]contact"),
    ("bodies", r"\bbod(y|ies)\b|body part|limb|hands?\b(?! (press|response))|point[- ]light|biological motion"),
    ("voices", r"\bvoices?\b|vocali[sz]|prosod|laughter|\bcry(ing)?\b|scream"),
    ("speech", r"\bspeech\b|spoken|syllables?|phonem|vowels?|consonant"),
    ("pseudowords", r"pseudo[- ]?words?|non[- ]?words?|pseudohomophone"),
    ("sentences", r"sentences?|stories|story|narratives?|passages?|texts?\b|discourse"),
    ("words", r"\bwords?\b|nouns?|verbs?|adjectives?|lexical"),
    ("letters", r"\bletters?\b|alphabet|characters?\b"),
    ("digits_numbers", r"\bdigits?\b|numbers?|numerals?|arithmetic|equations?|dots? arrays?"),
    ("money", r"money|monetary|\$|dollars?|euros?|coins?|points\b|reward cue|gain|loss"),
    ("food", r"\bfood|meals?|snacks?|milkshake|juice|sucrose|chocolate|drinks?\b"),
    ("drug_cues", r"alcohol|beer|wine|cigarette|smoking|tobacco|nicotine|cocaine|cannabis|marijuana|heroin|drug[- ]related|drug cues?"),
    ("tastes", r"\btastes?\b|gustatory|sweet|bitter|salty|umami|quinine"),
    ("odors", r"odou?rs?|olfactory|smell"),
    ("pain_heat", r"pain|noxious|heat|thermal|painful|laser|cold pressor|capsaicin"),
    ("electrical", r"electric(al)? (stimulation|shock)|shocks?\b|tens\b|median nerve"),
    ("touch_vibration", r"tactile|touch|vibrat|brush|air[- ]puff|somatosensory|pressure"),
    ("tones", r"\btones?\b|beeps?|clicks?|pure[- ]tone|chirps?|noise bursts?|white noise"),
    ("music", r"music|melod|chords?|songs?|rhythm"),
    ("environmental_sounds", r"environmental sounds?|natural sounds?|animal sounds?"),
    ("video", r"videos?|movies?|films?|clips?|animations?|cartoons?"),
    ("scenes_places", r"scenes?|places?|houses?|landscapes?|buildings?|rooms?"),
    ("objects_tools", r"objects?|tools?|artifacts?|items?\b"),
    ("animals", r"animals?|insects?|spiders?|snakes?"),
    ("emotional_pictures", r"iaps|affective pictures?|emotional (pictures?|images?|scenes?)|aversive (pictures?|images?)|erotic"),
    ("pictures", r"pictures?|images?|photo(graph)?s?|drawings?|line drawings?"),
    ("abstract_shapes", r"shapes?|geometric|fractals?|patterns?|abstract|symbols?|glyphs?|kanji|chinese characters"),
    ("gratings_dots", r"gratings?|gabors?|random[- ]dot|dots?\b|motion coherence|kinematogram"),
    ("checkerboard", r"checker[- ]?board|flicker"),
    ("fixation_cue", r"fixation|cross[- ]?hair|arrows?|cues?\b"),
    ("virtual_environment", r"virtual|maze|navigation|game environment"),
    ("social_feedback", r"feedback from (peers|others)|social feedback|likes?\b|ratings? (by|from) (peers|others)|cyberball"),
]
AFFECT = [("negative", r"fear|angry|anger|sad|disgust|threat|aversive|negative|unpleasant|pain|shock|hostile|violent"),
          ("positive", r"happy|smil|positive|pleasant|reward|erotic|appetiti|joy|amus"),
          ("neutral", r"neutral")]
SOCIAL = r"fac(e|es|ial)|eyes?|gaze|bod(y|ies)|voices?|people|persons?|social|partners?|players?|others?\b|avatars?|peers?"
MEASURES = [("rt", r"reaction times?|response times?|\brts?\b|latenc"), ("accuracy", r"accura|correct|errors?|hit rates?|false alarms?|commission|omission"),
            ("d_prime", r"d'|d-prime|dprime|sensitivity index|signal detection"), ("ssrt", r"ssrt|stop[- ]signal reaction"),
            ("ratings", r"ratings?|rated|likert|vas\b|visual analog|valence|arousal|liking|wanting|craving|intensity"),
            ("choices", r"choices?|choose|chose|decisions?|acceptance|offers?|gambl|risk|bets?"),
            ("learning", r"learning rate|learning curve|acquisition|reversal|trials to criterion|model[- ]based"),
            ("recall_recognition", r"recall|recogni|remember|memory performance|hits"),
            ("physiology", r"skin conductance|scr\b|heart rate|pupil|eye[- ]?tracking|emg|cortisol|startle"),
            ("count_fluency", r"number of words|words generated|fluency|count")]
AXES = [("load", r"load|set size|n-back|\d-back|difficulty|complexity|memory set"),
        ("valence_emotion", r"valence|emotion|affect|expression|fear|threat|negative|positive"),
        ("congruency_conflict", r"congruen|interference|conflict|compatib|flanker|stroop"),
        ("reward_value", r"reward|incentive|monetary|gain|loss|value|magnitude|outcome"),
        ("probability_risk", r"probabil|risk|uncertain|ambigu"),
        ("delay_time", r"delay|interval|soa|timing|duration|tempo"),
        ("stimulus_category", r"category|categories|faces? (vs|versus)|houses?|objects?|words? (vs|versus)|stimulus type"),
        ("cue_validity_attention", r"valid|cue|attend|attention|orienting"),
        ("go_nogo_stop", r"go\b|no-?go|stop|inhibit"),
        ("self_other_social", r"self|other|social|familiar|partner|in-?group|out-?group"),
        ("instruction_regulation", r"regulat|reappra|suppress|instruct|strategy|look\b|decrease|increase"),
        ("repetition_novelty", r"repeat|repetition|novel|old|new|familiar"),
        ("modality", r"modality|auditory vs|visual vs|crossmodal|multisensory|audiovisual"),
        ("intensity_dose", r"intensity|temperature|dose|contrast level|coherence|loudness"),
        ("switch_rule", r"switch|rule|shift|repeat trials")]


def _first(table, text):
    t = (text or "").lower()
    for v, p in table:
        if re.search(p, t):
            return v
    return None


def _all(table, text):
    t = (text or "").lower()
    return [v for v, p in table if re.search(p, t)]


def stimulus_facets(stimuli):
    kinds, affect, social, sets = [], set(), False, []
    for s in stimuli or []:
        c = s.get("content") or ""
        k = _first(STIMULUS_KIND, c)
        if k:
            kinds.append({"value": k, "source": c, "modality": s.get("modality"), "role": s.get("role")})
        for a in _all(AFFECT, c):
            affect.add(a)
        social |= bool(re.search(SOCIAL, c.lower()))
        if s.get("stimulus_set"):
            sets.append(s["stimulus_set"])
    if len(affect) > 1:
        aff = "mixed"
    else:
        aff = next(iter(affect), None)
    return {"stimulus_kind": kinds, "stimulus_affect": aff, "stimulus_social": social, "stimulus_sets": sets}


def measure_facets(measures):
    return sorted({v for m in measures or [] for v in _all(MEASURES, m)})


def axis_facets(factors, conditions=None):
    out = set()
    for f in factors or []:
        txt = (f.get("factor") or "") + " " + " ".join(f.get("levels") or [])
        out.update(_all(AXES, txt))
    return sorted(out)


def build_facets(m):
    sf = stimulus_facets(m.get("stimuli"))
    resp = m.get("response") or []
    d = m.get("design") or {}
    return {
        **sf,
        "stimulus_modality": sorted({s.get("modality") for s in m.get("stimuli") or [] if s.get("modality")}),
        "response_effector": sorted({r.get("effector") for r in resp if r.get("effector")}),
        "response_kind": sorted({r.get("kind") for r in resp if r.get("kind")}),
        "n_alternatives": sorted({r.get("n_alternatives") for r in resp if isinstance(r.get("n_alternatives"), int)}),
        "speeded": any(r.get("speeded") == "yes" for r in resp),
        "judgment": m.get("judgment") or [],
        "design_type": d.get("type"),
        "adaptive": d.get("adaptive") == "yes",
        "feedback": [f for f in (m.get("feedback") or []) if f != "none"],
        "measures": measure_facets(m.get("measures")),
        "manipulation_axes": axis_facets(m.get("manipulated_factors")),
    }
