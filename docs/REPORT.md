# Task extraction, normalization and lineage: overnight report (2026-10-09)

**Two pages built from this pipeline** (hosted as private claude.ai artifacts):
- **Paradigm Atlas**, https://claude.ai/artifact/GN6pnjUpo9yoPYmZf8SpSE: one page per canonical task (224 in use)
  with naming variants, condition design, qualifiers, origin papers, labs, and related tasks.
- **Task Finder**, https://claude.ai/artifact/DP62s5Kxp9SJgKGy13f3R6: faceted search over 9,829 extracted tasks
  (7,261 neuroimaging, 2,568 behavioral psychology). Filter by paradigm, stimuli, response, design or condition
  axes, then copy the matching PMIDs.

The pipeline extracts descriptions of experimental tasks from papers. It then normalizes them into a layered task
identity and a set of queryable facets, and links tasks to each other through the papers they cite and the labs
that run them. Every number below comes from a script in `scripts/`. The chronological lab notebook of hypotheses
and tests was kept in the working directory and is not part of this repository.

## 1. Pipeline

```
paper text (ns-pond pubget/Elsevier/ACE, Europe PMC OA psych)
  │  taskcat/sections.py: sectionize, then pick task-relevant Methods passages (~13% of the text, 93% of task evidence)
  ▼
Extractor: fine-tuned NuExtract3 (4B, QLoRA on 4×3070), template = TaskMention (verbatim, grounded)
  │  v2: two passes. LIST {name, entity_kind, setting}, then DETAIL per task (stimuli, response, conditions,
  │  factors, design timing, measures, instructions, judgment, citations+role, modification)
  ▼
Normalizer (taskcat/normalize.py, lexicon.py, decompose.py, facets.py)
  │  gate: experimental task / rest / passive / naturalistic / localizer / neuropsych test / questionnaire /
  │        intervention / not a task
  │  identity: family → paradigm stem → canonical task (hed-task id or tct_* extension) → variant (hedvar)
  │            → qualifiers by axis (stimulus_content, stimulus_modality, response_modality, design, adaptation)
  │  routes:   A lexical · B procedure classifier (names masked) · C citation lineage · D senior-author reuse
  │  facets:   stimulus kind/affect/social/set, response effector/kind, judgment, design, feedback, measures, axes
  ▼
TaskCards (+ study_schema-shaped Task/Assessment records via taskcat/to_study_schema.py)
  │  citations resolved to PMIDs through each paper's XML bibliography (explicit xref links) or Europe PMC
  │  authors from PubMed (API key): ORCID, affiliations
  ▼
Relations: shares-origin-ref, same senior author, same stem/family, task-task similarity (procedure/co-citation/lab)
```

## 2. Results

### Extraction (TaskMention)
| system | task P | task R | F1 | verbatim grounding |
|---|---|---|---|---|
| NuExtract3 zero-shot | .745 | .366 | .491 | .951 |
| fine-tune v1 (1,178 Luna silver papers) | .747 | .534 | .623 | .984 |
| fine-tune v2 (two-pass LIST + DETAIL) | .727 | .520 | .606 | .984 |
| v2 ∪ grounded TaskExtractor names | .713 | .551 | .622 | — |
| **fine-tune v3** (v2 + 1 epoch on neuro + psych silver) | .755 | .558 | **.641** | .987 |
| Luna (teacher, 12-paper pilot) | .789 | .789 | .789 | .947 |

The reference is gpt-6-astra on 150 held-out papers. I suspected v1's recall gap came from long task lists that
never fit the 6k-token training window, so v2 extracts in two passes. That hypothesis was refuted: v2 made exactly
as many predictions as v1. On task-like entries both students recall about 63% of astra's tasks, against about 78%
for their Luna teacher on a small pilot, and recall of questionnaires and tests is about 40%. The gap is
teacher/data quantity. Next step: a few hundred papers labeled by the strongest model or by a human, with an
emphasis on recall. v2 was used for the scale-up because its short outputs are robust and fast (~44 papers/min on 4×3070). **v3 is
now the best model.** It continues v2 for one epoch with 139 psych silver papers added. On neuroimaging it gains
recall and citations; on 30 held-out psych papers the task-level score is within noise of v2 (.709 vs .734), but
fields improve markedly (conditions .67 vs .58, stimulus modality .79 vs .70). Weights are in
`ft/merged-task-v3` on beast.

### Normalization (canonical task)
The gold set is 450 TaskExtractor mentions labelled by expert-prompted annotator agents under hed-task's
procedure-first rules. Only the held-out batch was scored on a frozen snapshot:

| | coverage | exact | exact-or-alt | family | ≥2 routes agree |
|---|---|---|---|---|---|
| held-out batch 2 (150, frozen v2) | .757 | .821 | .872 | .949 | .906 |
| **unbiased batch 3 (150, annotated against inventory v3; current normalizer)** | .766 | .821 | **.916** | .874 | **.949** |
| batches 0–2 (used for tuning, optimistic) | .795 | .809 | .867 | .934 | .931 |

Against inventory v3 (about 200 canonical tasks: 107 hed-task, ~80 corpus extensions, 14 BrainMap-derived),
only 4.7% of gold mentions need a new procedure (25% against v2). The remaining gap is coverage, not inventory.
A second annotator agreed 100% with the first, but both are the same model, so that agreement is only an upper
bound. Human double-annotation is still needed.

Across the whole TaskExtractor corpus (39,096 mentions), 61% get a canonical task and 6% are gated out as
non-tasks or questionnaires; the remaining third is residue, clustered in `residue_clusters.json`.

### Hypotheses tested
| # | hypothesis | result |
|---|---|---|
| H1 | Raw names map onto Cognitive Atlas | **No.** 17% exact; names compose paradigm, stimulus and manipulation |
| H3 | Methods-passage selection keeps the task evidence | **Yes.** 93% of non-rest task spans kept in 13–15% of the text |
| H2 | Task citations resolve to PMIDs | **Yes.** 83% via Europe PMC; ~88% via local XML xref links |
| H4 | The procedure alone (names masked) predicts the paradigm | **Yes.** 77% task / 87% family over 108 classes (chance 24%); 96% at 50% coverage |
| H5 | Sharing a cited reference means the same paradigm | **Yes.** 40% vs 1.6% random (25×) |
| H6 | Citations alone can label a mention | **Partly.** 66% task / 77% family at 43% coverage; best used as corroboration |
| H7 | Labs reuse paradigms | **Yes.** Same senior author 19% vs random 1.8% (10×) |
| H8 | Corpus citations rediscover a paradigm's origin paper | **Partly.** Top-1 is the curated origin in 55% of tasks, top-5 in 70%; the rest are meta-analyses or seminal fMRI versions |
| H9 | Data-driven task similarity recovers expert families | **Locally yes.** Nearest neighbour is in the same family 64% (procedure) / 48% (co-citation) / 45% (lab) vs 7% chance; flat partitions don't match (low ARI) |
| H11 | Citation role can be predicted from the citing sentence and sharpens lineage | **Yes.** Lineage-vs-other 72% acc; filtering raises same-task concordance from 41% to 57% and citation-only labeling from 65% to 73% |
| H12 | In-corpus task citations form adaptation chains | **Yes.** The cited corpus paper runs the same task 58% (67% with role filter), same family 80%; hubs match known origins (Ochsner 2002 reappraisal, Delgado 2000 card guessing, LaBar 1998 fear conditioning) |
| H10 | The inventory covers behavioral psychology | **No.** 28% of psych gold mentions needed a NEW paradigm (5% in neuroimaging). After adding ~35 psych paradigms: 75% coverage, 79–80% accuracy (91% in neuroimaging) |
| H13 | Typed citation roles separate lineage from shared materials | **Yes.** Papers sharing an *origin* citation run the same task 63% of the time (88% same family); *prior-use* 47%; *stimulus-set* only 8%, since databases like IAPS cross paradigms |

### Conditions and contrasts
Each condition name is normalized to a kind (study_schema ConditionKind), trial phases, and axis:value atoms
(congruency, load, go/no-go/stop, switch, cue validity, novelty, emotion, valence, arousal, outcome, magnitude,
regulation, self/other, stimulus class, CS+/−, trial type …). The reading depends on the task: "neutral" means
no-outcome in MID and congruency-neutral in Stroop. Per-task condition schemas built from these atoms reproduce
the textbook designs: n-back load {0,1,2,3}, Stroop/flanker congruency, MID gain/loss × phase, CS+/CS−, and
regulation {look, reappraise, increase, suppress} × valence. Gold check on 200 conditions: kind 97%, atom
precision 90%, recall 74% (v1). The context-aware v2 raises recall to about 83%, re-scored on the same gold.
Contrasts become signed atom differences ("incongruent > congruent" → congruency: incongruent − congruent).
Apply this only to analyses linked to task conditions.

### Scale
- Extracted with the fine-tuned model: 150 gold papers, 1,324 psych papers and 2,800 ns-pond papers (about 4,300
  papers in ~2.5 GPU-hours), plus 1,200 Luna-silver papers. In total 13.6k TaskCards, 9,871 of them task-like and
  deduplicated.
- The TaskExtractor corpus (39k mentions) is normalized by the same normalizer: 64% get a canonical task.
- LLM budget: Luna 4.56M in / 1.93M out (all silver labels); astra 0.52M / 0.23M (gold reference).

## 3. Design decisions
- **Grounded extraction, separate canonicalization.** pondie showed that letting the extractor "name the
  paradigm" produces composed names found in no paper. Every extracted string must be a substring of the source;
  ungrounded values are dropped. v1 grounding is 98.4%.
- **Task identity = procedure** (hed-task inclusion test). Stimulus swaps, population, drug and recording modality
  are qualifiers or facets, not new tasks.
- **Layered identity.** Paradigm stem (e.g. stroop) ⊃ canonical task (hedtsk_emotional_stroop) ⊃ variant ⊃
  qualifiers. Queries can work at any level: "all Stroop", "all emotional-content tasks", "drug Stroop only".
- **Typed, multi-axis relations, not one hierarchy.** H9 shows tasks relate by procedure, stimulus domain, battery
  co-use and research programme.
- **Citation role matters.** Only task_origin, adapted_from, prior_use and stimulus_set citations drive lineage.
  Rest-network and analysis references (Biswal, Fox, Smith 2009) appear next to task names and are noise.
- **study_schema alignment.** `schema/study_schema_crosswalk.md` maps every field, records divergences D1–D17 as
  future study_schema changes, and `to_study_schema.py` emits compatible records.

## 4. What's next / open problems
1. **Extractor recall** (63% of astra's task-like entries). The two-pass format did not help, so the gap is the
   amount and quality of supervision. Options: a few hundred strongest-model or human labels focused on recall;
   self-consistency (union of LIST samples); the v3 domain-adapted run (results in `logs/v3_eval.txt` on beast).
2. **Behavioral-psychology inventory.** 28% of psych mentions needed new paradigms. About 35 were added, and the
   long tail remains (video occlusion, multiple-object avoidance, statistical sampling, Virtual Tools, …). Proposal:
   an explicit "bespoke procedure" bucket plus periodic residue clustering with human curation, rather than
   enumerating everything.
3. **Human validation.** Every gold set so far was made by annotator agents (same model family; their 100% mutual
   agreement is an upper bound). The highest-value next step is ~100 human-labelled mentions and ~100 human-checked
   conditions.
4. **Lineage coverage.** Only 11% of task cards have a resolved origin PMID. Remaining fixes: ACE/PDF-only papers
   with no XML bibliography (Europe PMC refs fetch at scale), and author-year markers without years.
5. **Contrasts.** Apply `normalize_contrast` to analyses linked to conditions (study_schema `Analysis.effect.cells`)
   rather than to analysis names.
6. **study_schema upstreaming.** Divergences D1–D20 in `schema/study_schema_crosswalk.md`. The main ones:
   entity_kind, a paradigm_id CURIE, a Stimulus class with role and stimulus set, effector/kind response split,
   factors on Task, timing, typed TaskReference roles, Condition.levels (axis:value), trial phases.
7. **Explorer and Finder.** Both are static snapshots. If you want people to curate the inventory (accept or rename
   proposed paradigms), I can rebuild the Atlas as a page with a shared review queue.
