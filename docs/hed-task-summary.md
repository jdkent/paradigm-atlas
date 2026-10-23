# hed-task (HED Task Catalog): technical summary

Source: <https://github.com/hed-standard/hed-task>, commit `1815e8c` (2026-09-25), shallow-cloned and read locally. Published site: <https://www.hedtags.org/hed-task/>. HED schema facts come from `hed-standard/hed-schemas`, `standard_schema/hedtsv/HED8.4.0/HED8.4.0_Tag.tsv`. In this repo HEDLatest.xml is 8.4.0.

All paths below are relative to the repo root unless stated otherwise.

---

## 1. Purpose and philosophy

### What it is

From `README.md`:

> A curated catalog of standard cognitive and behavioral neuroscience tasks and the cognitive processes they engage, developed as part of the HED (Hierarchical Event Descriptors) standardization effort. Its purpose is to provide a controlled vocabulary for tagging datasets with what their participants were asked to do, so that repositories can be searched by task or by process and datasets can be compared across laboratories.

Current size: **103 tasks plus 4 pseudo tasks (107 records)**, **19 task families**, **172 cognitive processes** in **19 process categories**, **486 task-process links**, and **776 named variations**. Every task and process is mapped to the Cognitive Atlas, and every task to CogPO.

### Definition of a task

From `docs/source/introduction.md`:

> A **task** is an "instructed activity": a set of goals to be achieved or a set of actions to be performed, or a combination of these, under conditions the experimenter controls, so that what participants do can be attributed to the mental processes the task was designed to engage.

Admission criteria (`docs/source/methods/task_criteria/01_task_selection_criteria.md`, section 1.1). A task is a structured paradigm that:

> 1. **Produces psychobiological time series data and event markers.** The paradigm generates a sequence of discrete, time-stamped events (sensory presentations, participant or sensory agent actions, brain dynamic events, experiment control events, experiment structure events, measurement events) that can be annotated with HED tags.
> 2. **Has a specified, reproducible procedure.** ... Generic task categories such as "memory task" or "attention task" are not specified tasks - rather, they are more general task domains.
> 3. **Is widely used in cognitive/behavioral neuroscience.** ...
> 4. **Engages identifiable cognitive processes.** ...

The criteria exclude self-report instruments (BDI, STAI), clinical screening tools, broad categories ("working memory task"), one-off designs, and neurological examinations.

### Core reasoning: identity comes from procedure, not construct

The main design decision is that a task's identity is set by its **procedure**. The cognitive construct it is claimed to measure does not decide identity. From `docs/source/methods/task_criteria/03_the_task_inclusion_test.md`:

> The procedure is the most important part. Two experiments with different manipulations or measurements but the same procedure are instances of the same task. Two experiments with different procedures are different tasks, even if they target the same cognitive construct.

Processes sit on a separate axis, linked to tasks but kept out of the task's definition. Task families are a third, browsing-only axis: "A family is a browsing aid, not a claim about mechanism" (`introduction.md`).

### Three levels of description

The repo places itself between CogPO and HED (`introduction.md`, "Resources at 3 granularities"):

| Resource | Labels | Example, for a Stroop experiment |
|---|---|---|
| The Catalog | a task, the goal in eliciting cognitive processes | Stroop Color-Word Task |
| CogPO | a condition: stimulus, response, instruction | colored color words, key press, "name the ink color" |
| HED | an event, with its time | the onset of the word RED printed in blue, 2.35 s into the run |

### How a task is decomposed

The schema does **not** break a task into stimulus/response/instruction/timing/agent/goal slots. The actual decomposition is:

- **Identity**: `canonical_name`, `aliases`, `hedtsk_id`.
- **Prose**: `short_definition` and `description`.
- **Inclusion test**: `procedure` (ordered free-text steps naming stimuli, responses and instructions), `manipulations` (independent variables with typical levels in parentheses) and `measurements` (dependent variables or signals). This is the operational core.
- **Variations**: named sub-paradigms that change the event structure.
- **Families**: what the participant does, with exactly one primary family and any number of secondary ones.
- **Process links**: what the task is designed to probe.
- **References** and **external mappings** (Cognitive Atlas, CogPO).

Stimulus, response and instruction attributes exist only as **proposed "facets"** (`data/facet_defs.tsv`). From `introduction.md`:

> whether and how the Catalog adopts facets is not yet decided, and no task record carries one.

The planned facets are: "the six CogPO-derived ones (stimulus modality, kind and role; response modality and kind; instructions), followed by the Catalog's own (trial structure, feedback, timing and primary measure)". Timing, trial structure, feedback and primary measure have **no vocabulary yet**.

Agent and goal are not explicit fields. "Goal" is folded into the task definition ("what the participant was asked to do"). Agents appear only in HED event-level tags (`Agent-task-role/Experiment-participant`, etc.).

---

## 2. Schema and vocabulary

### Files

| File | Content |
|---|---|
| `data/task_details.json` | 107 task records (bare JSON array) |
| `data/schemas/task_details.schema.json` | JSON Schema (draft-07) for tasks |
| `data/process_details.json` | 172 processes and 19 categories |
| `data/schemas/process_details.schema.json` | JSON Schema for processes |
| `data/task_family_defs.tsv` | 19 families: `family_id`, `order`, `name`, `scope` |
| `data/facet_defs.tsv` | Proposed facet vocabularies. Columns: `facet value label definition source cogpo_id hed_tags hed_note` |
| `data/mappings/*.tsv` | Cognitive Atlas and CogPO crosswalks (see section 4) |
| `data/atlas_summary.json`, `data/cogpo_summary.json` | Harvested summaries of the Atlas and CogPO OWL/wiki |
| `docs/source/methods/task_criteria/*.md` | Selection, naming, inclusion-test, variation, borderline and family rules |
| `docs/source/methods/process_criteria/*.md` | Process selection, naming, definition, category, reference and linkage rules |

### Task record (`data/schemas/task_details.schema.json`)

Required fields: `hedtsk_id`, `canonical_name`, `short_definition`, `description`, `inclusion_test`, `families`, `hed_process_ids`.

| Field | Type / constraint | Meaning |
|---|---|---|
| `hedtsk_id` | `^hedtsk_[a-z][a-z0-9_]*$` | Deterministic slug of the canonical name ("Task"/"Test" stripped) |
| `canonical_name` | string ending in "Task" or "Test" | "Use the most widely recognized name"; "Prefer the specific paradigm name over the generic process name (e.g., "Eriksen Flanker Task" not "Response Conflict Task")" |
| `task_kind` | enum `task` \| `pseudo_task` (omitted means `task`) | Pseudo task = "a block-level activity that serves the experiment around it rather than eliciting a process through a trial structure" |
| `aliases` | string[] | Abbreviations, eponyms, short forms, instrument-specific names. "Aliases are **not** variations." |
| `short_definition`, `description` | string | Prose |
| `inclusion_test.procedure` | string[] (≥1) | "Ordered steps of what the participant does, each a sentence." |
| `inclusion_test.manipulations` | string[] (≥1) | "What the experimenter varies, one independent variable per item." |
| `inclusion_test.measurements` | string[] (≥1) | "What is recorded, one dependent variable or signal per item." |
| `variations[]` | `{variation_id, name, description, justification}` | `variation_id` = `hedvar_<task slug>__<variation slug>` |
| `families[]` | `{family_id, role: primary\|secondary, confidence: high\|review, rationale}` | Exactly one primary. A rationale is required on a secondary or a `review` entry. |
| `hed_process_ids[]` | `^hed_[a-z][a-z0-9_]*$` | Must resolve to `process_details.json`. Non-empty unless pseudo task. |
| `references[]` | `roles` enum `historical, review, experiment, dataset, other, unknown`; `ids` {doi, openalex_id, pmid, pmcid, s2_id, arxiv_id}; `oa_status` (OpenAlex enum + `unknown`); `verified_on`, `confidence`, `citation_string` ... | Bibliographic records. In practice 383 roles are `unknown` and 276 `historical`. |
| `source_task_numbers`, `status` | int[], string (`complete`) | Editorial bookkeeping |

The inclusion test is used as a membership rule (`03_the_task_inclusion_test.md`, section 3.2):

> A specific experiment is an instance of a given task if and only if:
> 1. Its procedure matches the **procedure** steps ...
> 2. It manipulates at least one variable from the **manipulations** list
> 3. It records at least one measure from the **measurements** list

### Process record (`data/schemas/process_details.schema.json`)

- **Process fields**: `process_id` (`hed_<slug>`), `process_name` (sentence case), `categories[]` (one primary plus any secondaries, same shape as families), `definition`, `notes`, `aliases[]` (objects `{name, note}`), `references[]`, `tasks[]` (derived), `task_count`.
- **Category fields**: `category_id`, `name`, `scope`, `out_of_scope`, `issues`, `history`, `process_count`.

Admission test for a process (`introduction.md`):

> a mental operation hypothesized to occur during a trial ... something with an identifiable onset, an eliciting condition and an in-principle measurable signature. ... States and traits, specific emotions, stimulus categories, individual-difference constructs, task parameters, analysis methods and umbrella terms such as "attention" or "memory" are excluded.

Example process record, verbatim minus references:

```json
{
 "process_id": "hed_interference_control",
 "process_name": "Interference control",
 "categories": [{"category_id": "inhibitory_control_and_conflict_monitoring", "role": "primary", "confidence": "high"}],
 "definition": "Resistance to interference from task-irrelevant stimuli or competing response representations, measured by Stroop, Flanker, and Simon effects.",
 "tasks": [ "...9 tasks: ANT, Emotional Stroop, Flanker, IAT, N-Back, Navon, OSPAN, Simon, Stroop..." ],
 "task_count": 9,
 "aliases": [{"name": "interference resolution"}]
}
```

**The 19 process categories** (with counts of processes filed there as primary): associative_learning_and_reinforcement (13), auditory_and_pre_attentive_deviance_processing (4), awareness_agency_and_metacognition (13), cognitive_flexibility_and_higher_order_executive_function (3), emotion_perception_and_regulation (5), face_and_object_perception (12), implicit_and_statistical_learning (2), inhibitory_control_and_conflict_monitoring (9), language_comprehension_and_production (16), long_term_memory (21), motor_preparation_timing_and_execution (16), perceptual_decision_making_evidence_accumulation (1), reasoning_and_problem_solving (11), reward_anticipation_and_motivation (6), selective_and_sustained_attention (11), short_term_and_working_memory (9), social_cognition_and_strategic_social_choice (11), spatial_cognition_and_navigation (2), value_based_decision_making_under_risk_and_uncertainty (7).

**The 172 process IDs**: hed_acoustic_processing, hed_action_initiation, hed_active_maintenance, hed_affective_priming, hed_alerting, hed_analogical_reasoning, hed_antisaccade, hed_approach_motivation, hed_associative_learning, hed_attention_shifting, hed_attentional_awareness, hed_attentional_capture, hed_auditory_perception, hed_auditory_tone_discrimination, hed_autobiographical_memory, hed_avoidance_motivation, hed_biological_motion_perception, hed_body_ownership, hed_categorization, hed_causal_reasoning, hed_choice_commitment, hed_chunking, hed_cognitive_reappraisal, hed_competition, hed_conflict_monitoring, hed_consolidation, hed_cooperation, hed_declarative_memory, hed_deductive_reasoning, hed_delay_discounting, hed_depth_perception, hed_directed_forgetting, hed_discourse_processing, hed_divided_attention, hed_effort_allocation, hed_emotion_recognition, hed_emotion_regulation, hed_encoding, hed_episodic_memory, hed_error_correction, hed_error_detection, hed_executive_attention, hed_expressive_suppression, hed_extinction, hed_face_identity_recognition, hed_face_perception, hed_familiarity, hed_feature_based_attention, hed_feeling_of_knowing, hed_fine_motor_control, hed_forgetting, hed_goal_directed_behavior, hed_goal_maintenance, hed_grasping, hed_gustatory_perception, hed_habit, hed_hypothesis_testing, hed_imitation, hed_implicit_memory, hed_in_group_out_group_processing, hed_incentive_salience, hed_inductive_reasoning, hed_insight, hed_instrumental_conditioning, hed_interference_control, hed_interoceptive_awareness, hed_intertemporal_choice, hed_joint_attention, hed_judgment_of_learning, hed_language_comprehension, hed_language_production, hed_lexical_access, hed_manipulation, hed_masking, hed_mathematical_reasoning, hed_means_ends_analysis, hed_mental_rotation, hed_metacognitive_control, hed_metacognitive_monitoring, hed_mind_wandering, hed_model_based_learning, hed_model_free_learning, hed_motion_perception, hed_motor_memory, hed_motor_planning, hed_motor_preparation, hed_motor_sequence_learning, hed_motor_timing, hed_naming, hed_object_based_attention, hed_olfactory_perception, hed_orienting, hed_pattern_completion, hed_pattern_recognition, hed_pattern_separation, hed_pavlovian_conditioning, hed_perceptual_awareness, hed_perceptual_decision_making, hed_perspective_taking, hed_phonological_awareness, hed_phonological_encoding, hed_pitch_perception, hed_planning, hed_policy_learning, hed_proactive_control, hed_proactive_interference, hed_probability_judgment, hed_procedural_memory, hed_proprioception, hed_prospective_memory, hed_reaching, hed_reactive_control, hed_reading, hed_recall, hed_reciprocity, hed_recognition, hed_recollection, hed_reconsolidation, hed_rehearsal, hed_reinforcement_learning, hed_response_conflict, hed_response_execution, hed_response_inhibition, hed_response_selection, hed_retrieval, hed_retroactive_interference, hed_reversal_learning, hed_reward_anticipation, hed_reward_consumption, hed_reward_prediction_error, hed_risk_processing, hed_saccade, hed_selective_attention, hed_self_monitoring, hed_self_other_distinction, hed_self_referential_processing, hed_semantic_knowledge, hed_semantic_memory, hed_semantic_processing, hed_sense_of_agency, hed_sentence_comprehension, hed_set_shifting, hed_social_decision_making, hed_social_perception, hed_somatosensory_perception, hed_source_memory, hed_spatial_attention, hed_spatial_memory, hed_spatial_working_memory, hed_speech_perception, hed_speech_production, hed_stereotyping, hed_strategy_use, hed_subgoaling, hed_sustained_attention, hed_syntactic_parsing, hed_temporal_attention, hed_valuation, hed_value_based_decision_making, hed_value_learning, hed_verbal_fluency, hed_verbal_memory, hed_verbal_working_memory, hed_visual_form_recognition, hed_visual_object_recognition, hed_visual_perception, hed_visual_working_memory, hed_visuomotor_adaptation, hed_vocal_motor_control, hed_word_recognition, hed_working_memory, hed_working_memory_updating.

### Task-process linkage rules (`docs/source/methods/process_criteria/06_task_linkage_rules.md`)

> A link from task T to process P should satisfy at least one of:
> - **Canonical link:** The paradigm-defining paper(s) for T theorize that T engages P. Example: Stroop -> interference control.
> - **Contrast-based link:** Some condition contrast in T is standardly interpreted as isolating P. Example: congruent vs. incongruent in Stroop -> conflict monitoring.
> - **Measurement-based link:** T has a measure standardly interpreted as an index of P. Example: stop-signal reaction time in the Stop-Signal Task -> response inhibition.
>
> A link is not an ontology assertion (no `is-a`, no class hierarchy). A link is not an exclusion - other processes may be engaged; we list only those the task is designed to probe.

### Task families (`data/task_family_defs.tsv`, verbatim scope column)

| family_id | scope |
|---|---|
| conflict_and_interference | A task-relevant feature must be reported while a task-irrelevant feature of the same stimulus or of a distractor pulls toward a competing response; the cost on incongruent trials is the measure. |
| response_inhibition | A prepared or prepotent response must be withheld or cancelled on a minority of trials; commission errors and stopping latency are the measures. |
| attentional_cueing | A cue precedes a target and predicts its location or identity with some validity; the benefit of valid over invalid cues is the measure. |
| visual_search_and_tracking | A target must be found among, or followed through, a field of distractors; search slopes, detection accuracy or tracking capacity are the measures. |
| oddball_and_vigilance | A long stream of stimuli contains rare targets or deviants; detection, false alarms, response variability or the evoked response to the rare event are the measures. |
| perceptual_judgment | A judgment about a sensory stimulus near or below threshold, or a passive presentation designed to isolate a perceptual response; thresholds, accuracy and evoked responses are the measures. |
| working_memory_span | A small set of items must be held, and sometimes manipulated, over a delay of seconds before a probe or reproduction; span, capacity or set-size effects are the measures. |
| recall_and_recognition | A study phase is followed, after minutes or longer, by a test that asks the participant to recall, recognize or attribute studied material; hits, false alarms and their decomposition are the measures. |
| memory_control | Encoding or retrieval is deliberately shaped by instruction: an item is to be forgotten, suppressed, related to the self, or an intention is to be executed later; ... |
| metacognition_and_interoception | The participant reports on their own cognition, action or body: confidence in future recall, the perceived time of an action, the sense that a limb or heartbeat is theirs; ... |
| conditioning_and_reinforcement | Contingencies between stimuli, actions and outcomes are learned from experience, with or without explicit instruction; learning curves, choice probabilities and perseveration are the measures. |
| motor_performance | Movement itself is the object: timing, sequencing, adaptation or speed of a well-specified response; ... |
| executive_and_reasoning | A rule must be discovered, applied, switched or used to plan a sequence of moves; switch costs, perseverative errors, solution accuracy and planning time are the measures. |
| reward_and_value_choice | Options differing in reward magnitude, probability, delay or effort are chosen between, or a cue announces a potential reward before a speeded response; ... |
| social_cognition_and_games | Another agent's mental state must be inferred, or money must be allocated between the participant and another player; ... |
| emotion | Affective stimuli are presented to elicit, recognize or regulate an emotional response; ... |
| language | Words, sentences or pictures are read, heard, named or generated; ... |
| spatial_navigation | A location or orientation in space must be learned, imagined or found; ... |
| pseudo_tasks | Block-level activities that serve the experiment around them rather than eliciting a process through trials: a resting block ..., a fixation block ..., a questionnaire ..., and feedback ... |

Each family scope is itself a short structural description: procedure skeleton, then "the measure". This pattern is useful as a template.

### Proposed facet vocabularies (`data/facet_defs.tsv`)

There are 134 values across 6 facets. Each row carries a CogPO id where one exists, the HED 8.4.0 tag(s), and a fit note. The `source` column is `cogpo`, `hed` or `catalog`, and records where each value came from.

**stimulus_modality (10)**: visual, auditory, tactile, olfactory, gustatory, interoceptive, electrical, pain, pressure, thermal. Representative rows, verbatim:

```
stimulus_modality  visual         Visual         The sensory modality that pertains to the sense of sight.  cogpo  COGPO_00132  Visual-presentation  Exact tag.
stimulus_modality  interoceptive  Interoceptive  The sensory modality that pertains to the sense of interoception, or internal sensations.  cogpo  COGPO_00128  (none)  HED 8.4.0 has Somatic-presentation and Vestibular-presentation but no interoceptive presentation tag.
stimulus_modality  pain           Pain           The subtype of tactile modality that pertains to the sense of pain.  cogpo  COGPO_00126  Somatic-presentation, Pain  Pain is a Somatic-attribute, so it qualifies the presentation rather than naming a modality.
```

**stimulus_kind (46; value → HED tag)**: three_dimensional_objects (3D-shape); abstract_patterns (Pattern); acupuncture (none); asian_characters (Character); braille_dots (Braille); breathable_gas (none); chord_sequences (Musical-sound); clicks (Click); digits (Character); electrical_stimulation (none); eye_puffs (none); faces (Face); false_fonts (Glyph); film_clips (Video-clip, Movie); fixation_point (Cross); flashing_checkerboard (Pattern); food (none); fractals (Pattern); heat (Tactile-temperature); infrared_laser (none); infusion (none); letters (Character); music (Musical-sound); noise (Signal-noise); nonverbal_vocal_sounds (Vocalized-sound); nonvocal_sounds (Environmental-sound); odor (none); pain (Pain); pictures (Image); points_of_light (Dots); pseudowords (Pseudoword); random_dots (Dots); reversed_speech (Vocalized-sound); shapes (2D-shape); syllables (Syllable); symbols (Glyph, Arrow); tactile_stimulation (none); tms (none); tones (Tone); vibratory_stimulation (Tactile-vibration); words (Word). Catalog additions: sentences (Sentence); scenes (Photograph); monetary_amounts (none); playing_cards (none); virtual_environment (Screen-window, Head-mounted-display).

**stimulus_role (12)**: target, non_target, feedback, reward (from CogPO), plus distractor, cue, oddball, penalty, go_signal, stop_signal, prime, novel (from HED). Example:

```
stimulus_role  stop_signal  A stimulus that instructs the participant to withhold a response already under way.  Stop-signal  From HED's Task-stimulus-role vocabulary.
```

**response_modality (11)**: hand, foot, mouth, face, arm (→ Upper-extremity), leg (→ Lower-extremity), shoulder, pelvis, eye, torso, finger (Catalog addition).

**response_kind (23)**: button_press (Press, Push-button), saccade, blink, speech (Speak), finger_tapping (Press, Finger), point, grasp, manipulate (Move-upper-extremity), draw (none), write, drink (none), swallow, breath_hold (Hold-breath), breathe, flexion_or_extension, micturate, smile, whistle; Catalog additions key_press (Press, Keyboard-key), mouse_click (Press, Mouse-button), touchscreen_tap (Touch, Touchscreen), rating (none: "the response is a Participant-response event carrying a value"), no_response (Passive).

**instructions (32)**: attend, count, detect, discriminate, encode, fixate, generate, imagine, move, name (→ Identify), read, recall, repeat, rest, sing, smile, track, breath_hold, breathe (from CogPO); judge, recognize, respond, predict, plan, learn, identify, switch_attention (from HED `Think`); choose (→ Judge, nearest), rate, withhold, navigate, play (Catalog additions; rate, withhold and navigate have no HED tag). Example:

```
instructions  withhold  To refrain from responding on signal.  (none)  No HED action; Stop-signal and Omitted-action describe the stimulus and the outcome. Added for Go/No-Go and Stop-Signal.
```

### Identifier conventions (`introduction.md`)

| Kind | Form | Example |
| --- | --- | --- |
| Task | `hedtsk_<slug>` | `hedtsk_stroop_color_word` |
| Task variation | `hedvar_<task slug>__<variation slug>` | `hedvar_stroop_color_word__counting_stroop` |
| Process | `hed_<slug>` | `hed_response_inhibition` |
| Process category | `<slug>` | `inhibitory_control_and_conflict_monitoring` |
| Task family | `<slug>` | `conflict_and_interference` |

"The `hed_` prefix ... is not a claim of HED schema membership." Identifiers are provisional.

---

## 3. The task catalog

### Tasks by family (`*` = secondary cross-listing)

- **conflict_and_interference**: Affective Priming*, Attention Network*, Emotional Stroop, Eriksen Flanker, Implicit Association, Navon, Simon, Stroop Color-Word, Weapons Identification, Imitation-Inhibition
- **response_inhibition**: Anti-Saccade, Go/No-Go, Stop-Signal, Sustained Attention to Response
- **attentional_cueing**: Attention Network, Dot-Probe, Posner Spatial Cueing
- **visual_search_and_tracking**: Contextual Cueing, Multiple Object Tracking, Useful Field of View, Visual Search, Rapid Serial Visual Presentation*
- **oddball_and_vigilance**: Continuous Performance, Mismatch Negativity, Oddball, Psychomotor Vigilance, Sustained Attention to Response*, Rapid Serial Visual Presentation
- **perceptual_judgment**: Auditory Masking, Biological Motion Perception, Cambridge Face Memory*, Face Processing, Mental Rotation*, Navon*, Random Dot Kinematogram, Visual Masking
- **working_memory_span**: Change Detection, Corsi Block-Tapping, Delayed Match-to-Sample, Digit Span, N-Back, Operation Span, Sternberg Item Recognition
- **recall_and_recognition**: Cambridge Face Memory, Free Recall, Mnemonic Similarity, Old/New Recognition Memory, Paired Associates Learning, Remember/Know, Rey Auditory Verbal Learning, Source Memory, Autobiographical Memory
- **memory_control**: Directed Forgetting, Think/No-Think, Prospective Memory, Self-Referential Encoding
- **metacognition_and_interoception**: Feeling-of-Knowing, Judgment-of-Learning, Heartbeat Detection, Body Ownership Illusion, Intentional Binding
- **conditioning_and_reinforcement**: Artificial Grammar Learning, Contextual Cueing*, Instrumental Conditioning, Multi-Armed Bandit, Pavlovian Fear Conditioning, Probabilistic Classification Learning, Probabilistic Selection, Reversal Learning, Serial Reaction Time, Two-Stage Decision, Causal Learning
- **motor_performance**: Digit Symbol Substitution, Finger Tapping, Mirror Tracing, Motor Sequence Learning, Psychological Refractory Period, Serial Reaction Time*, Trail Making*
- **executive_and_reasoning**: Raven's Progressive Matrices, Remote Associates, Task Switching, Tower of London, Trail Making, Wason Selection, Wisconsin Card Sorting
- **reward_and_value_choice**: Balloon Analog Risk, Delay Discounting, Iowa Gambling, Monetary Incentive Delay, Social Incentive Delay, Effort-Based Decision-Making
- **social_cognition_and_games**: Dictator Game, False Belief, Prisoner's Dilemma, Reading the Mind in the Eyes, Trust Game, Ultimatum Game, Weapons Identification*
- **emotion**: Affective Picture Viewing, Affective Priming, Emotion Regulation, Facial Emotion Recognition
- **language**: Lexical Decision, Phonological Awareness, Picture Naming, Remote Associates*, Semantic Priming, Sentence Comprehension, Verb Generation, Verbal Fluency, Self-Paced Reading
- **spatial_navigation**: Mental Rotation, Virtual Radial Arm Maze, Virtual Morris Water Maze
- **pseudo_tasks**: Rest, Fixate, Take Questionnaire, Receive Feedback

(Every canonical name ends in "Task", e.g. "Go/No-Go Task".) Per-task generated pages live at `docs/source/tasks/hedtsk_*.md`.

### Worked example 1: Stroop Color-Word Task (`data/task_details.json`, references omitted)

```json
{
 "hedtsk_id": "hedtsk_stroop_color_word",
 "canonical_name": "Stroop Color-Word Task",
 "aliases": ["Stroop", "Color-Word Interference Test", "CWIT"],
 "short_definition": "Naming the ink color of color words while ignoring word meaning; RT and error costs on incongruent trials index selective attention and conflict control.",
 "description": "The Stroop Color-Word Task is a classic measure of selective attention and cognitive control that requires participants to identify the ink color of printed words while ignoring the semantic content. In the standard version, participants view color names (e.g., \"RED,\" \"BLUE\") printed in incongruent ink colors and must respond with the ink color rather than reading the word. The task measures reaction time and accuracy across congruent trials (word and color match), incongruent trials (word and color conflict), and neutral trials. Performance reflects the ability to overcome automatic word-reading processes and requires engagement of executive control mechanisms. The Stroop interference effect (slowed RT on incongruent trials) is one of the most robust findings in cognitive psychology.",
 "inclusion_test": {
  "procedure": [
   "Color words (RED, BLUE) are printed in incongruent ink colors.",
   "Participants name the ink color while ignoring the word."
  ],
  "manipulations": [
   "Congruency (congruent, incongruent, neutral)",
   "Proportion congruent",
   "Response modality (vocal, manual)",
   "Stimulus type (classic, spatial, numerical)"
  ],
  "measurements": [
   "Stroop interference effect (incongruent − congruent RT)",
   "Facilitation (neutral − congruent)",
   "Error rate",
   "Conflict adaptation (Gratton effect)"
  ]
 },
 "variations": [
  {"name": "Classic Color-Word Stroop", "description": "Name ink color of incongruent color words; the canonical interference paradigm.", "justification": "Canonical color naming of congruent/incongruent color words", "variation_id": "hedvar_stroop_color_word__classic_color_word_stroop"},
  {"name": "Manual (Button-Press) Stroop", "description": "Responses via key press rather than vocal naming; preferred in neuroimaging to reduce motion artifacts.", "justification": "Button press instead of vocal response; different response modality", "variation_id": "hedvar_stroop_color_word__manual_button_press_stroop"},
  {"name": "Vocal Response Stroop", "description": "Original format with spoken color-naming responses; produces larger interference due to response-channel overlap with word reading.", "justification": "Vocal naming; distinct from manual version", "variation_id": "hedvar_stroop_color_word__vocal_response_stroop"},
  {"name": "Counting Stroop", "description": "Count the number of items displayed while ignoring the number word printed; used extensively in fMRI.", "justification": "Count number of words instead of naming color; different task dimension", "variation_id": "hedvar_stroop_color_word__counting_stroop"},
  {"name": "Spatial Stroop", "description": "Conflict between stimulus location and directional word content (e.g., \"LEFT\" on right side).", "justification": "Spatial word/location conflict; different conflict dimension", "variation_id": "hedvar_stroop_color_word__spatial_stroop"},
  {"name": "Numerical Stroop", "description": "Conflict between numerical magnitude and physical size of digits.", "justification": "Number magnitude vs. physical size conflict; different domain", "variation_id": "hedvar_stroop_color_word__numerical_stroop"},
  {"name": "Reverse Stroop", "description": "Read the word while ignoring ink color; reverses the typical control demand.", "justification": "Name the word rather than the color; reversed task demand", "variation_id": "hedvar_stroop_color_word__reverse_stroop"},
  {"name": "Proportion-Congruent Manipulation", "description": "Varying the ratio of congruent-to-incongruent trials to study context-driven control adjustments.", "justification": "Conflict frequency variation; adaptation context per §5.2", "variation_id": "hedvar_stroop_color_word__proportion_congruent_manipulation"},
  {"name": "Face-Word Stroop", "description": "Emotional face images paired with congruent/incongruent emotion labels.", "justification": "Face emotion vs. color word conflict; different stimulus domain", "variation_id": "hedvar_stroop_color_word__face_word_stroop"},
  {"name": "Color-Shape Stroop", "description": "Shapes printed in colors that conflict with shape-color associations (e.g., a blue banana).", "justification": "Color word/shape conflict instead of ink color; different conflict structure", "variation_id": "hedvar_stroop_color_word__color_shape_stroop"},
  {"name": "Priming Stroop", "description": "Preceded by neutral, congruent, or incongruent primes to study anticipatory control.", "justification": "Prime precedes Stroop item; temporal context manipulation", "variation_id": "hedvar_stroop_color_word__priming_stroop"},
  {"name": "Negative Priming Stroop", "description": "Measures inhibitory aftereffects when a previously ignored color word becomes the target on the next trial.", "justification": "Previously ignored item becomes target; tests ignored repetition effect", "variation_id": "hedvar_stroop_color_word__negative_priming_stroop"}
 ],
 "source_task_numbers": [1],
 "status": "complete",
 "families": [{"family_id": "conflict_and_interference", "role": "primary", "confidence": "high", "rationale": "Canonical interference task"}],
 "hed_process_ids": ["hed_interference_control", "hed_selective_attention", "hed_conflict_monitoring", "hed_response_inhibition", "hed_response_conflict", "hed_reading"]
}
```

A reference entry, verbatim (first of 7):

```json
{"title": "Studies of interference in serial verbal reactions.", "authors": "Stroop, J. R.", "year": 1935,
 "journal": "Journal of Experimental Psychology", "venue_type": "journal", "volume": "18", "issue": "6", "pages": "643-662",
 "ids": {"doi": "10.1037/h0054651", "openalex_id": "W2120357670", "pmid": null, "pmcid": null, "s2_id": "fa80a1cc...", "arxiv_id": null},
 "oa_status": "green", "source": "crossref", "confidence": "high", "verified_on": "2026-04-20", "roles": ["historical"]}
```

### Worked example 2: Monetary Incentive Delay Task (references omitted)

```json
{
 "hedtsk_id": "hedtsk_monetary_incentive_delay",
 "canonical_name": "Monetary Incentive Delay Task",
 "aliases": ["MID", "Monetary Incentive Delay"],
 "short_definition": "Cue predicts potential monetary gain or loss; speeded target response determines outcome. Striatal activity to cues indexes reward anticipation.",
 "description": "The Monetary Incentive Delay Task is the dominant paradigm for neuroimaging studies of reward anticipation and consumption. On each trial, a cue signals the potential outcome: reward (gain), loss avoidance, or neutral. After a variable delay period, participants respond to a briefly presented target; successful responses earn the reward (or avoid the loss). The critical contrast is neural activity during the anticipation period (cue-to-target), which robustly activates the ventral striatum/nucleus accumbens, versus the outcome period (after response), which more strongly engages ventromedial prefrontal cortex. The MID has been widely adopted in clinical neuroimaging of addiction, depression, and schizophrenia.",
 "inclusion_test": {
  "procedure": [
   "A cue signals potential reward, loss, or neutral outcome.",
   "After a delay, a target appears and participants make a speeded response.",
   "Outcome depends on response speed."
  ],
  "manipulations": [
   "Cue type (reward magnitude, loss magnitude, neutral)",
   "Target duration (titrated to ~66% hit rate)"
  ],
  "measurements": [
   "RT by cue condition",
   "fMRI activation in ventral striatum (anticipation) and medial PFC (outcome)",
   "Hit rate"
  ]
 },
 "variations": [
  {"name": "Standard MID (Knutson)", "description": "Gain, loss-avoidance, and neutral cues; target duration titrated to ~66% accuracy.", "justification": "Canonical cue-anticipation-response structure with monetary reward/punishment", "variation_id": "hedvar_monetary_incentive_delay__standard_mid_knutson"},
  {"name": "Graded Reward MID", "description": "Multiple reward magnitudes ($0.20, $1.00, $5.00) to parametrically modulate anticipatory activation.", "justification": "Multiple reward magnitude levels; tests reward sensitivity parametrically", "variation_id": "hedvar_monetary_incentive_delay__graded_reward_mid"},
  {"name": "MID with Social Rewards", "description": "Smiling faces or positive social feedback replace monetary outcomes (see also SID, Task 75).", "justification": "Social stimuli (faces) as rewards instead of money; different incentive type", "variation_id": "hedvar_monetary_incentive_delay__mid_with_social_rewards"},
  {"name": "MID with Drug Cues", "description": "Substance-related cues replacing monetary cues in addiction research.", "justification": "Drug-associated cues as incentive stimuli; different cue content", "variation_id": "hedvar_monetary_incentive_delay__mid_with_drug_cues"},
  {"name": "Passive MID", "description": "No motor response required; isolates anticipation without motor confounds.", "justification": "No response required; isolates anticipatory processing from motor preparation", "variation_id": "hedvar_monetary_incentive_delay__passive_mid"},
  {"name": "MID with Effort Component", "description": "Effortful responses (grip strength) to earn rewards; integrates motivation and effort.", "justification": "Effort required to obtain reward; adds effort-discounting to incentive structure", "variation_id": "hedvar_monetary_incentive_delay__mid_with_effort_component"}
 ],
 "source_task_numbers": [63],
 "status": "complete",
 "families": [{"family_id": "reward_and_value_choice", "role": "primary", "confidence": "high", "rationale": "Cue announces a potential monetary outcome before a speeded response"}],
 "hed_process_ids": ["hed_reward_anticipation", "hed_incentive_salience", "hed_approach_motivation", "hed_response_execution"]
}
```

### Worked example 3: Rest Task (pseudo task, references omitted)

```json
{
 "hedtsk_id": "hedtsk_rest",
 "canonical_name": "Rest Task",
 "task_kind": "pseudo_task",
 "aliases": ["Resting State", "Resting-State Recording", "Rest Block", "Baseline Rest"],
 "short_definition": "Participant stays awake, still and unoccupied for a block of several minutes while spontaneous activity is recorded; the block is a baseline for task blocks or a resting-state recording in its own right.",
 "description": "The participant is asked to remain awake and relaxed, to keep still, and to do nothing in particular while the recording runs, typically for three to ten minutes. No stimulus is presented for processing and no response is required. ... When a cross is merely provided and the instruction is to rest, the block is a Rest Task; when the instruction is to hold gaze on the target and gaze is monitored or required, it is a Fixate Task. Rest is a pseudo task: it establishes a state rather than eliciting a process, so it carries no process links.",
 "inclusion_test": {
  "procedure": ["Participant remains awake, still and relaxed with no stimulus to process and no response to make, for a block typically lasting 3 to 10 minutes."],
  "manipulations": ["Eye state (open or closed)", "Block duration", "Position relative to task blocks (before, between, after)", "Instruction to let the mind wander versus to stay alert"],
  "measurements": ["Spontaneous EEG or MEG spectra and microstates", "Resting-state fMRI connectivity", "Heart rate and respiration", "Self-reported drowsiness or thought content after the block. No behavioral performance measure"]
 },
 "variations": [
  {"name": "Eyes-Open Rest", "description": "Rest with eyes open, usually with a fixation cross or a blank screen.", "justification": "Eye state changes visual input and the EEG alpha rhythm; a different postural state for the whole block", "variation_id": "hedvar_rest__eyes_open_rest"},
  {"name": "Eyes-Closed Rest", "description": "Rest with eyes closed.", "justification": "Eye state changes visual input and the EEG alpha rhythm; removes eye-movement artifact and raises the risk of drowsiness", "variation_id": "hedvar_rest__eyes_closed_rest"}
 ],
 "families": [{"family_id": "pseudo_tasks", "role": "primary", "confidence": "high", "rationale": "Resting block; establishes a baseline state"}],
 "hed_process_ids": []
}
```

Shorter excerpts. N-Back procedure: `["A continuous stream of stimuli is presented.", "Participants indicate when the current item matches the one presented N items back."]`; manipulations `["Load level (N = 0, 1, 2, 3)", "Stimulus type (letters, locations, faces)", "Lure trials (N±1 matches)", "Dual N-back (two simultaneous streams)"]`; variations: Verbal, Spatial, Emotional, Dual, Fractal/Object, Adaptive, with Lures, Auditory. Ultimatum Game procedure: `["A proposer splits a sum of money.", "The responder can accept (both keep their shares) or reject (neither gets anything)."]`; manipulations include "Proposer identity (human, computer)".

---

## 4. Relation to HED, Cognitive Atlas, CogPO

### HED

The catalog sits **above** HED. "HED describes events; the Catalog describes the paradigm the events belong to." Catalog IDs are **not** HED schema terms, and "How task and process identifiers will be carried in HED annotations and in dataset metadata is not yet decided" (`introduction.md`). The history, from `docs/source/cogpo/hed_vs_cogpo.md`: HED-2G had a Paradigm hierarchy, and HED-3G removed it "because the available paradigm nomenclature is not standardized". All that remains is `Metadata-identifier/CogAtlas/#` and `Metadata-identifier/CogPo/#`. Robbins et al. 2022 called for "a task specification meta-code to enable comparison of events on the basis of their function and value in the context of the task", and the page says "That is the gap the Catalog exists to fill." Current tagging guidance (`how_to_use_the_catalog.md`) is to record the `hedtsk_` id, the optional `hedvar_` id, and the `hed_` process ids.

### CogPO (Turner & Laird 2012)

- `data/mappings/hed_task_to_cogpo.tsv` (107 rows; exact 24, close 22, related 26, none 35) and `cogpo_paradigm_to_hed.tsv` (86 rows: 83 OWL classes + 3 wiki-only; exact 27, close 15, related 8, none 36). Reverse rows carry `scope_class`: `paradigm | broad_class | pseudo_task | physiological | motor_act | imaging_protocol`, plus `match_level` (task or variation).
- Example rows:
  - `COGPO_00092 Stroop Task Paradigm ... paradigm exact task hedtsk_stroop_color_word ... "Same paradigm. CogPO folds in Counting Stroop (a Catalog variation) and Emotional Stroop (a separate Catalog task, mapped here as close)."`
  - `hedtsk_mismatch_negativity ... close COGPO_00072 Auditory Oddball Paradigm ... "A passive auditory oddball; CogPO has no MMN class and no passive-oddball distinction."`
- CogPO's six dimension vocabularies seed the facets. In `hed_vs_cogpo.md` each dimension maps to one HED subtree:

| CogPO dimension | HED 8.4.0 subtree |
|---|---|
| Stimulus Modality | `Property/Sensory-property/Sensory-presentation` |
| Explicit Stimulus | `Item` (`Face`, `Word`, `Tone`, `Dots`, `Pattern`, `Image`, ...) |
| Stimulus Role | `Property/Task-property/Task-stimulus-role` and `Task-event-role/Feedback` |
| Response Modality | `Item/Biological-item/Anatomical-item/Body-part` |
| Overt Response | `Action` (`Press`, `Saccade`, `Speak`, `Grasp`, `Write`, ...) |
| Instructions | `Action/Think` and `Action/Perform` |

  "88 of the 102 CogPO values have a HED 8.4.0 tag."
- On CogPO's unit of description (`hed_vs_cogpo.md`): the condition is "a planned process which must include at least one stimulus, one instruction, and one response type". CogPO represents "what was intended by the experimenters ... and not what the subject may have actually perceived". CogPO deliberately excludes cognitive processes. The Catalog "takes the other side of that bargain".
- Gaps in HED that the authors list as candidate schema proposals: an interoceptive presentation; items for digit/number, food, odorant, speech-as-stimulus, checkerboard and fixation point; actions tap, draw, drink, name, choose/decide and rate; body parts Arm and Leg.

### Cognitive Atlas

- It was the starting corpus. The Atlas task list "was narrowed to paradigms that produce event-structured data, its concepts were reshaped into processes", and a gap analysis added 15 paradigms.
- Mappings in `data/mappings/`, with `match_type` meaning `exact | close | related | none` (`docs/source/methods/atlas_mapping_method.md`: "`close`: The same family, but the Atlas entry is a variant, is broader, or is narrower"; "`related`: The Atlas has entries in the same area but none that corresponds"):
  - `hed_task_to_atlas.tsv` 103 rows (70/11/4/18)
  - `atlas_task_to_hed.tsv` 857 rows (86/73/24/674)
  - `hed_process_to_atlas.tsv` 172 rows (102/14/23/33)
  - `atlas_concept_to_hed.tsv` 918 rows (102/14/16/786)
- Example: `hedtsk_stroop_color_word  exact  trm_4b1968619b00b  color-word stroop task ... "Generic Stroop task tsk_4a57abb949e27 also exists"`; `hedtsk_n_back exact tsk_4a57abb949bcd ... "Eight n-back variants exist as separate Atlas entries"`.
- Comparison (`docs/source/atlas/the_catalog_vs_the_atlas.md`): 4.72 processes per task vs the Atlas's 1.66 concepts per task. The Atlas has 1398 KINDOF/PARTOF concept edges and 1585 contrast definitions, and the Catalog has **no** relations between processes and no contrasts. Conclusion: "the Atlas is an excellent source of candidate terms and stable identifiers, and a poor source of automatic answers." Names cannot be matched automatically, and every row was hand-checked.

---

## 5. Task relationships: families, variants, paradigms

The catalog has **no is-a / kind-of hierarchy among tasks**. Relationships are expressed four ways:

1. **Family membership** (many-to-many, primary/secondary, with rationale and a `review` flag). Example: Navon is primary in conflict_and_interference and secondary in perceptual_judgment, "because the global-local judgment is also a perceptual one" (`06_task_family_assignment.md`). Families are defined by procedure skeleton, and "Families are organizational, not a hierarchy."
2. **Variations** (task → named sub-paradigm, 776 in total). The test for a variation (`04_variation_criteria.md`):

   > If you compared the event logs from the standard version and the variation, would there be structural differences in the types of events, their temporal organization, or the participant's required responses?

   Genuine variations change the response modality, stimulus configuration, cognitive demand (1-choice vs go/no-go), task structure (blocked vs interleaved when it changes what must be tracked), add participant actions, change the S-R mapping (pro vs anti-saccade), or name a sub-paradigm (Sally-Anne, Smarties).

   **Not variations** (the "DROP" codes): MEAS (recording modality: "with fMRI", "with EEG"), ANAL (analysis: DDM, ROC), DESG (blocked vs event-related, ISI/SOA sweeps, parametric difficulty, set size), STIM (equivalent stimulus-set swap: IAPS→OASIS, translated lists), POPL (population), IDIF (individual differences), TRAN (training), PHAR (drug), SCOR (scoring), ALIA (alias), MOTI (incentive add-on), DUAL (concurrent secondary task). EMOT was retired: emotional versions are kept as variations.
3. **Separate tasks that are de facto variants of another.** Emotional Stroop is a top-level task. Its description begins "A variant of the classic Stroop in which participants name the ink color of words that vary in emotional valence". The link to Stroop exists only in prose and through the shared family (conflict_and_interference) and shared processes. The SID/MID link appears only as text: "see also SID, Task 75". The borderline policy (`05_borderline_case_policy.md`) keeps a named paradigm "with its own literature" as its own task.
4. **Shared process links** (task ↔ process, many-to-many). Two tasks are related if they probe the same process. This is the stated route for cross-task grouping: "Two datasets tagged with different tasks that share a process can be grouped for a question about that cognitive process."

Recorded borderline policies (`05_borderline_case_policy.md`) worth reusing:

- Proportion-congruent manipulations are kept as variations (open question).
- Child versions are kept only if the procedure changes.
- Dual-task add-ons are always dropped.
- Confidence ratings are dropped as MEAS, except for the Heartbeat Detection confidence-accuracy paradigm.
- A computerized version counts as a variation only if the sensory or motor modality changes. eCorsi is kept. Stylus-on-tablet vs pencil-on-paper TMT is dropped.

Feedback rule (`01_task_selection_criteria.md` section 1.3): feedback that is essential to learning (RL, reversal, gambling) is part of the task's procedure. Incidental feedback is the separate pseudo task Receive Feedback.

---

## 6. HED schema (8.4.0): task-relevant top-level tags

Extracted from `hed-schemas/standard_schema/hedtsv/HED8.4.0/HED8.4.0_Tag.tsv`. Descriptions are quoted from the `dc:description` column, sometimes truncated.

**Event**: "Something that happens at a given time and (typically) place." Children:

- `Sensory-event` ("Something perceivable by the participant. An event meant to be an experimental stimulus should include ... Experimental-stimulus")
- `Agent-action`
- `Data-feature`
- `Experiment-control`
- `Experiment-procedure` ("as in performing a saliva swab ... or administering a survey")
- `Experiment-structure` ("change-point of the structure of experiment ... change in experimental conditions or tasks")
- `Measurement-event`

**Agent**: `Animal-agent`, `Avatar-agent`, `Controller-agent`, `Human-agent`, `Robotic-agent`, `Software-agent` (e.g. "an AI advisor"). Related, under `Property/Agent-property`:

- `Agent-state` → `Agent-cognitive-state` (Alert, Anesthetized, Asleep, Attentive, Awake, Brain-dead, Comatose, Distracted, Drowsy, Intoxicated, Locked-in, Passive, Resting, Vegetative), `Agent-emotional-state`, `Agent-physiological-state`, `Agent-postural-state`
- `Agent-task-role` → Experiment-actor, Experiment-controller, Experiment-participant, Experimenter
- `Agent-trait` → Age, Agent-experience-level, Ethnicity, Gender, Handedness, Race, Sex

**Action**: top level `Communicate`, `Move`, `Perceive`, `Perform`, `Think`.

- `Think`: Allow, Attend-to, Count, Deny, Detect, Discriminate, Encode, Evade, Generate, Identify, Imagine, Judge, Learn, Memorize, Plan, Predict, Recall, Recognize, Respond, Switch-attention, Track. This is effectively the instruction vocabulary.
- `Perform`: Close, Collide-with, Halt, Modify, Open, Operate, Play, Read, Repeat, Rest, Ride, Write.
- `Move`:
  - Breathe (Blow, Cough, Exhale, Hiccup, Hold-breath, Inhale, Sneeze, Sniff)
  - Move-body (Bend, Dance, ..., Turn)
  - Move-body-part (Move-eyes, Move-face, Move-head, Move-lower-extremity, Move-torso, Move-upper-extremity). Press, Saccade, Fixate, Blink and Grasp sit under these.
- `Communicate`: gestural (Smile, Nod-head, Thumb-up, ...), musical (Hum, Sing, Whistle, ...), vocal (Speak, Whisper, Shout, ...).

**Item**:

- `Biological-item` (Anatomical-item → Body-part; Organism)
- `Language-item`: Character, Clause, Glyph, Nonword, Paragraph, Phoneme, Phrase, Pseudoword, Sentence, Syllable, Textblock, Word
- `Object`: Geometric-object, Ingestible-object, Man-made-object, Natural-object
- `Sound`:
  - Environmental-sound (Crowd-sound, Signal-noise)
  - Musical-sound (Instrument-sound, Tone, Vocalized-sound)
  - Named-animal-sound
  - Named-object-sound (Alarm-sound, Beep, Buzz, Click, ...)

**Property/Sensory-property**:

- `Sensory-attribute`:
  - Auditory: Loudness, Pitch, Sound-envelope, Sound-volume, Timbre
  - Gustatory: Bitter, Salty, Savory, Sour, Sweet
  - Olfactory
  - Somatic: Pain, Stress
  - Tactile: pressure, temperature, texture, vibration
  - Vestibular
  - Visual: Color, Luminance, Luminance-contrast, Opacity
- `Sensory-presentation`:
  - Auditory-presentation (Monophonic, Stereophonic, Silent, Loudspeaker-separation)
  - Gustatory, Olfactory, Somatic, Tactile, Vestibular
  - Visual-presentation (2D-view, 3D-view, Background-view, Bistable-view, Foreground-view, Foveal-view, Map-view, Peripheral-view)

**Property/Task-property** ("Something that pertains to a task"). This is the most task-relevant subtree:

- `Task-action-type` ("How an agent action should be interpreted in terms of the task specification"): Appropriate-action, Correct-action, Correction, Done-indication, Imagined-action, Inappropriate-action, Incorrect-action, Indeterminate-action, Miss, Near-miss, Omitted-action ("An expected response was skipped."), Ready-indication.
- `Task-attentional-demand`: Bottom-up-attention, Covert-attention, Divided-attention, Focused-attention, Orienting-attention, Overt-attention, Selective-attention, Sustained-attention, Switched-attention, Top-down-attention.
- `Task-effect-evidence`: Behavioral-evidence, Computational-evidence, External-evidence, Intended-effect.
- `Task-event-role` ("The purpose of an event with respect to the task"): Cue, Experimental-stimulus, Feedback, Incidental, Instructional, Mishap, Participant-response, Task-activity, Warning.
- `Task-relationship`: Background-subtask, Primary-subtask.
- `Task-stimulus-role`: Distractor, Expected, Extraneous, Go-signal, Meaningful, Newly-learned, Non-informative, Non-target, Not-meaningful, Novel, Oddball, Penalty, Planned, Priming, Query, Reward, Stop-signal, Target, Threat, Timed, Unexpected, Unplanned.

**Property/Organizational-property** (design structure): Collection, `Condition-variable` ("Task-conditions are sometimes called independent variables or contrasts"), `Control-variable`, Def/Def-expand/`Definition`, Event-context, Event-stream, `Experimental-intertrial`, `Experimental-trial`, `Indicator-variable` ("sometimes called dependent variables"), Recording, `Task` ("An assigned piece of work, usually with a time allotment"), `Time-block`.

**Timing**:

- `Temporal-value`: Delay/#, Duration/#, Time-interval/#, Time-value/#
- `Temporal-marker`: Inset, Offset, Onset, Pause, Time-out, Time-sync

**Other**:

- `Environmental-property`: Augmented-reality, Indoors, Motion-platform, Outdoors, Real-world, Rural, Terrain, Urban, Virtual-world
- `Informational-property/Metadata/Metadata-identifier`: `CogAtlas/#`, `CogPo/#`, DOI, OBO-identifier, ...

Library schemas in hed-schemas: lang, mouse, score, slam, testlib. None of them is task-specific.

Note: HED's Condition-variable / Control-variable / Indicator-variable trio mirrors the Catalog's manipulations / (implicit controls) / measurements. HED gives only the slots, though, with no controlled values.

---

## 7. Strengths and gaps for a paper-extraction and meta-analysis task schema

### Strengths to adopt

1. **Procedure-first identity plus a decidable inclusion test.** Procedure, manipulations and measurements, with the "iff" rule, is a good template for an LLM or curator deciding "is this paper's task an instance of X?". It maps directly to extraction slots.
2. **A principled variation-vs-new-task-vs-irrelevant rule.** The event-log test and the 12 DROP codes (MEAS, ANAL, DESG, STIM, POPL, IDIF, TRAN, PHAR, SCOR, ALIA, MOTI, DUAL) cleanly separate task identity from things a meta-analysis wants recorded *as separate fields* (imaging modality, population, drug, analysis). This is ready-made guidance on which paper attributes belong to the task and which to the study.
3. **Three orthogonal axes**: task (procedure), family (browsing by procedure skeleton) and process (construct, many-to-many, with canonical, contrast or measurement justification). Keeping construct out of task identity avoids the circularity of reverse inference.
4. **Facet vocabularies with HED and CogPO crosswalks** (`data/facet_defs.tsv`). These are closed lists for stimulus modality, kind and role, response modality and kind, and instructions, and they are directly usable as enums for extraction. Each value has a HED tag, so extraction output can align with BIDS/HED event annotation.
5. **Curated crosswalks** to the Cognitive Atlas (task and concept IDs) and CogPO (BrainMap lineage), with exact/close/related/none match types and notes. These are useful for joining to NeuroSynth/NeuroVault/BrainMap-style resources.
6. **Aliases** for name normalization (e.g. "CWIT" and "Color-Word Interference Test" both map to Stroop). This is useful for entity linking from paper text.
7. **Pseudo tasks** (rest, fixation, questionnaire, feedback) as first-class labels for block types that papers report.
8. **Family scope statements** written as "procedure skeleton; the measure is X". These are a good pattern for category definitions.

### Gaps and limitations

1. **Facets are not populated.** "No task record carries facet values." There are no per-task stimulus, response or instruction annotations, so you cannot query the catalog by stimulus or response features yet. You would need to fill these yourself, ideally per variation and per condition, not per task.
2. **Inclusion-test content is free text.** Manipulations like "Congruency (congruent, incongruent, neutral)" and measurements like "Stroop interference effect (incongruent − congruent RT)" are prose strings with no typing (variable name, levels, within/between, DV type, contrast definition). For meta-analysis you would want structured conditions and contrasts. The Cognitive Atlas has 1585 contrast definitions and the Catalog has none.
3. **No timing or design vocabulary.** Trial structure, SOA/ISI, stimulus duration, block vs event-related, number of trials/runs and feedback schedule are planned facets ("trial structure, feedback, timing and primary measure") with no vocabulary. DESG explicitly removes design choices from task identity, so they need a home at the study or experiment level in your schema. HED's `Temporal-value`, `Experimental-trial`, `Time-block` and `Condition-variable` give slots but no values.
4. **Agent, goal and social structure are implicit.** There are no fields for agent roles (partner human vs computer, as in the PD/UG "Proposer identity (human, computer)" manipulation), the participant's goal or instruction text, or the incentive structure. HED has `Agent-task-role` and `Software-agent`, but the catalog does not use them.
5. **Task-to-task relationships are weak.** There is no is-a or variant-of between top-level tasks: Emotional Stroop → Stroop exists only in prose. Families are flat, non-hierarchical and explicitly "not a claim about mechanism". There is no "paradigm class" layer (e.g. interference task → Stroop/Flanker/Simon) beyond the family. For categorization you may want an explicit hierarchy or a set of feature-based (facet) definitions so that families become inferable rather than asserted.
6. **No process-process relations.** Processes are grouped into categories only, with no KINDOF/PARTOF edges (the Atlas has 1398). Umbrella and specific processes coexist without links (e.g. `hed_working_memory` and `hed_working_memory_updating`).
7. **Process links are coarse.** They are binary and per task, not per variation or per contrast, and carry no evidence pointer per link (the justification type, canonical vs contrast vs measurement, is not stored).
8. **Small, curated scope.** There are 103 tasks vs 857 in the Atlas. The Catalog excludes questionnaires, batteries, naturalistic paradigms (film viewing, music, story listening), imagery, counting/calculation, reading aloud, deception, video games and olfaction (the Catalog lacks 15 of CogPO's task-shaped paradigms), and has no task with gustatory stimuli. Neuroimaging papers often use exactly these (localizers, naturalistic viewing), so expect many unmappable tasks.
9. **The variation vs STIM distinction may hurt stimulus queries.** Swapping stimulus sets is explicitly not a variation, so stimulus content (faces vs words, emotional vs neutral) is only partly captured by variations (e.g. "Emotional N-Back", "Face-Word Stroop"). A meta-analysis schema should record stimulus content as facets regardless of variation status.
10. **Some measurement items mix behavior and imaging** (e.g. "fMRI activation in ventral striatum (anticipation) and medial PFC (outcome)"), which goes against the catalog's own MEAS rule. Reference roles are mostly `unknown` (383 of 662 role tags).
11. **Instability.** IDs are provisional, the facet adoption question is open, and how IDs will be carried in HED/BIDS is undecided.
12. **HED vocabulary holes** relevant to extraction, self-reported in `hed_vs_cogpo.md`: no interoceptive presentation; no digit/number, food, odor or speech-as-stimulus items; no tap, draw, drink, name, choose/decide or rate actions; no Arm/Leg. Choice and rating responses, which are central to decision tasks, have no HED action.

### Suggested synthesis

Use the Catalog as the **task-identity layer**: `hedtsk_` / `hedvar_` IDs, aliases, families, process links and Atlas/CogPO crosswalks. Use `facet_defs.tsv` as the **seed enums** for stimulus, response and instruction, attached per condition (CogPO-style). Then add your own structured layers for:

- conditions and contrasts (named levels, within/between)
- timing and design (block/event-related, durations, SOA, trial counts, feedback schedule)
- agents and incentives
- the DROP-code attributes as study-level metadata: measurement modality, population, pharmacology, analysis, dual-task add-on, incentive add-on, and stimulus set

Pair HED tags with each enum value where they exist, so extracted descriptions can line up with BIDS/HED event annotations.
