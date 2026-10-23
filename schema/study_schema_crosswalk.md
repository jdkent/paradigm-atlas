# task_schema ↔ study_schema crosswalk

Against: study_schema main `74da550` (`neuroimaging-study-storage/task.yaml`), and the unmerged branch
`origin/claude/gallant-shannon-dhsj8u` (`7482dd1`, 2026-10-09). Covers task_schema v0.1 (`schema/task_schema.yaml`).

The rule: every TaskMention field either maps to an existing study_schema slot (**same**), maps to one by a
deterministic function (**derivable**), or is a **divergence**. Each divergence is listed in the last section
as a study_schema change to make later. `taskcat/to_study_schema.py` implements the same and derivable rows. It emits study_schema-shaped Task and
Assessment records and keeps the divergent fields under `_taskcat`.

## Field map (TaskMention → study_schema `Task` / `Condition`)

| task_schema | study_schema | relation | notes |
|---|---|---|---|
| `name` (verbatim) | `Task.name` | same | Both are the source's own words. |
| `paradigm_term` (verbatim) | branch `Task.paradigm` | same (branch) | Both require the source's own words and stay empty otherwise (the rewritten wording in task-schema-proposal.md). |
| `description` | `Task.description` | same | |
| `instructions` (verbatim) | `Task.instructions` | same | |
| `stimuli[].content` | `Task.stimuli` (free text) + branch `Task.stimulus_content` | derivable | `Task.stimuli` = join of contents. `stimulus_content` = normalized stimulus_kind (Layer 2). |
| `stimuli[].modality` | `Task.stimulus_modality` | derivable | Union over stimuli. Our extra values `nociceptive`, `thermal`, `vestibular`, `electrical`, `multimodal` → **divergence D3**. |
| `stimuli[].stimulus_set` | — | **divergence D4** | Named stimulus database (IAPS, NimStim…). |
| `stimuli[].role` | — | **divergence D5** | HED Task-stimulus-role values. |
| `response[].effector` + `response[].kind` | `Task.response_modality` | derivable | See the mapping below. Keeping effector and kind separate follows CogPO/BrainMap (Response Modality vs Response Type) → **divergence D6**. |
| `response[].n_alternatives`, `speeded` | — | **divergence D7** | |
| `conditions[].name` | `Condition.name` | same | |
| `conditions[].kind` | `Condition.condition_kind` | derivable | task→`task_state`, control→`control_state`, baseline→`control_state`, rest→`rest`, fixation→`fixation`. The training template is being renamed to study_schema's values. |
| `manipulated_factors[]` | `ModelTerm`/`FactorLevel` (analysis side) | **divergence D8** | study_schema stores factors only when a model term was extracted. Ours are a task property. |
| `design.type` | `Task.design_type` | same | Same 4 values. `unknown` → unset. |
| `design.{n_runs,n_trials,stimulus_duration,trial_duration,isi_iti,total_duration,adaptive}` | — (older StudyIESchema had timing) | **divergence D9** | |
| `entity_kind` | — (Task vs Assessment split) | derivable + **divergence D1** | questionnaire_or_scale / neuropsychological_test with setting outside_imaging → `Assessment`. Other kinds → `Task`. The kind itself is not stored. |
| `setting` | implied by Task vs Assessment | derivable | |
| `judgment` | — | **divergence D10** | Instruction verbs (CogPO/BrainMap Instructions, hed-task `instructions` facet). |
| `feedback` | — | **divergence D11** | |
| `measures` | `Task.performance_measures` | same | |
| `software` | `Task.presentation_software` | same | |
| `citations[].marker` | `Task.references` | same | Both verbatim. |
| `citations[].role` | — | **divergence D12** | The branch's `reference_ids` has no role. Lineage needs one: only task_origin/adapted_from/prior_use should drive `paradigm_category`. |
| resolved citation PMIDs | branch `Task.reference_ids` | same (branch) | Filled by `taskcat/citations.py` (Europe PMC). |
| `modification` (verbatim) | branch `variant_qualifiers` (partly) | **divergence D13** | Qualifiers come from the name. `modification` is the paper's own statement of how it departs from the cited version. |
| TaskCard `canonical_task` / `families` | branch `Task.paradigm_category` | derivable (branch) | We use hed-task ids plus corpus-derived ids. The branch uses a free string → **divergence D2**. |
| TaskCard facets | — | **divergence D14** | Query facets. Could live in a sidecar instead of the storage schema. |

### ResponseModality derivation

| (effector, kind) | study_schema ResponseModality |
|---|---|
| (hand_finger, button_press/keyboard/mouse_or_touch/joystick/rating_scale) | `button_press` |
| (hand_finger or whole_body, movement/grip_force/writing_drawing) | `hand_movement` |
| (vocal, speech) | `speech` |
| (eye, saccade/eye_fixation) | `eye_movement` |
| (foot, *) | `foot_or_leg_movement` |
| (face, *) or (vocal, non-speech) | `oral_nonspeech` |
| (none_covert, *) or kind=no_response | `covert_response` if the instructions demand covert processing, else `none` |

## Divergences: changes to make in study_schema later

| id | proposal | why |
|---|---|---|
| D1 | `Task.entity_kind` (open enum: experimental_task, resting_state, passive_stimulation, naturalistic, localizer, …) | Needed to filter non-tasks (TaskExtractor emitted "DTI", "VBM analysis", "404 not found" as tasks) and to separate rest/passive/naturalistic from paradigms. |
| D2 | `Task.paradigm_id` (CURIE: `hedtsk:`, `cogat:`, corpus id) next to `paradigm_category` | A string category can't be joined to hed-task or Cognitive Atlas. |
| D3 | Extend `StimulusModality` with nociceptive, thermal, vestibular, electrical | Pain/thermal paradigms are common, and hed-task facet_defs already has pain, thermal and electrical. |
| D4 | `Task.stimulus_sets` (multivalued, verbatim) | IAPS/NimStim/KDEF are strong lineage and query keys. |
| D5 | `Stimulus` class {content, modality, set, role} replacing the free-text `Task.stimuli` | A meta-analysis queries by stimulus role (cue vs feedback vs target). |
| D6 | Split `response_modality` into effector + response_kind | CogPO/BrainMap make this split. A rating given by button press is neither "button_press" alone nor "rating" alone. |
| D7 | `n_response_alternatives`, `speeded` | Classic paradigm discriminators (2-AFC vs go/no-go). |
| D8 | Factors on `Task` (`Task.factors: [{name, levels}]`) | task-condition-normalization.md: only 21% of contrast cells reach a Condition. Factors on the task are recoverable from Methods without any model term. |
| D9 | Timing block (n_runs, n_trials, durations, ISI/ITI, adaptive) | A query need ("event-related with ISI < 2 s"), and timing was present in StudyIESchema. |
| D10 | `Task.judgments` (instruction verbs) | The instruction is the core of task identity in hed-task's inclusion test. |
| D11 | `Task.feedback` | Separates reward and learning paradigms from perception ones. |
| D12 | `TaskReference {marker, role, resolved_id}` replacing `references: string` | Role-typed citations: origin vs prior use vs stimulus set vs analysis method. |
| D13 | `Task.modification` (verbatim) | The paper's own statement of how its version departs from the original. Grounded, unlike composed qualifiers. |
| D14 | Facet sidecar (`TaskCard`) | Derived and normalized. It could live outside the storage schema as a deterministic view. |

## Additions after v0.1 (2026-10-09)

| task_schema (TaskCard) | study_schema | relation | notes |
|---|---|---|---|
| `stem` (taskcat/decompose.py STEMS) | branch `Task.paradigm_category` | derivable (branch) | The stem groups canonical tasks that share a procedure skeleton (stroop = color-word + emotional). It is the right grain for `paradigm_category`. |
| `canonical_task` (hed-task/tct id) | — | **divergence D2** (see above) | Finer than the stem. Keeps hed-task's identity decisions (Emotional Stroop is its own task). |
| `variant` (hedvar id) | — | **divergence D15** | hed-task named variations. |
| `qualifiers[{text, axis}]` | branch `variant_qualifiers[TaskQualifier{text, axis}]` | same (branch) | Axis values = branch `TaskVariantAxis` (stimulus_content, stimulus_modality, response_modality, design, adaptation) plus our `population` and `other` → **divergence D16** (two extra axis values). Our qualifiers come from the name words left after removing the canonical name, so they are grounded in the name. |
| `entity_kind` = `neuropsychological_test` | `Assessment` vs `Task` | derivable | Single neuropsych tests (digit span, TMT) keep a canonical id; batteries get none. |
| typed task relations (same_stem, same_family, shared_stimulus_kind, co_cited_origin, same_lab) | — | **divergence D17** | Corpus-level graph, not per-record. Belongs in a derived table, not the storage schema. |

### Conditions and contrasts (taskcat/conditions.py)

| task_schema | study_schema | relation | notes |
|---|---|---|---|
| condition `kind` | `Condition.condition_kind` | same | Same values (task_state, control_state, rest, fixation). |
| condition `atoms` [axis:value] | `Condition.stimulus_content` (stimulus-axis atoms only); `FactorLevel` (other axes) | derivable + **divergence D18** | Atoms are the factor levels a condition sits at (congruency:incongruent, load:2, outcome:gain …). study_schema records factors only through extracted ModelTerms, so the factor-level reading of a condition name is lost. Proposal: `Condition.levels: [{axis, value}]` with an open axis vocabulary seeded from conditions.ATOMS. |
| condition `phases` | — | **divergence D19** | Trial phase (cue, anticipation, outcome, encoding, retrieval …). Needed to separate e.g. MID anticipation from outcome contrasts. |
| per-task condition schema (axes × levels seen across the corpus) | — | **divergence D20** | Corpus-derived, like Cognitive Atlas "conditions" per task. Belongs in a derived table keyed by canonical task. |
| contrast `signature` {axis: (pos, neg)} | `Analysis.effect.cells` (term, level, direction) | derivable | A cell's (level, direction) pairs reduce to the signature once levels carry atoms. This needs D18. |
