# How experimental tasks/paradigms have been formally described and categorized

Literature and resource review, 2026-10-09. Written for the taskCategories project (extract, normalize and classify task mentions from the psych/neuro literature for meta-analysis queries).

**What was checked directly:**
- **CogPO:** OWL file downloaded and parsed.
- **BrainMap:** taxonomy pages scraped.
- **Cognitive Atlas:** live REST API queried, plus the full Neo4j export in `CognitiveAtlas/legacy_cogat_linkml`.
- **HED 8.4.0:** `Tag.tsv` parsed.
- **hed-task:** repo read.
- **NIF-Investigation.ttl:** read.
- **Experiment Factory:** configs read.
- **Self_Regulation_Ontology:** variable file read.
- **NeuroVault:** API fields read.
- **TaskExtractor:** schema read.
- **Papers:** citations confirmed through PubMed metadata or the publisher or arXiv pages.

Anything marked *(not re-verified)* comes from background knowledge and was not checked during this session.

---

## 0. Summary table

| Resource | Unit described | Facets | # tasks/classes | Inter-task relations | Download |
|---|---|---|---|---|---|
| CogPO (Turner & Laird 2012) | paradigm → conditions | stimulus modality, stimulus type, response modality, response type, instructions | 83 paradigm classes; 41 stimulus types; 17 overt response types; 17 instructions; 10 stim modalities; 8 response modalities (FMA) | `is_a` (only Oddball has subclasses) | OWL: `http://www.cogpo.org/ontologies/CogPOver1.owl` (works); BioPortal `COGPO`; NIF copy `ttl/external/CogPO.ttl` |
| BrainMap taxonomy (Fox et al. 2005; current site) | experiment (contrast) + its conditions | Context, Paradigm Class, Behavioral Domain, Stimulus Modality/Type/Content/Laterality, Response Modality/Type/Laterality, Instruction | **115 paradigm classes** (each with definition + "First"/"Most" citation); 71 behavioral-domain entries (5 top domains) | none between paradigm classes (flat); BD is a 3-level hierarchy | Vocabulary is public on brainmap.org/taxonomy; coded data come through Sleuth or a collaborative-use agreement |
| Cognitive Atlas (Poldrack et al. 2011) | task (+ conditions, contrasts, indicators, implementations, datasets, batteries, citations) | free-text definitions; concept assertions through contrasts; 10 concept classes | 857 tasks on the site (853 in the LinkML dump), 918 concepts, 44 collections | task `kind_of` (67 edges), task `part_of` (51 edges), `in_battery`; task→concept `asserts`/"measures" through a contrast | REST `https://www.cognitiveatlas.org/api/v-alpha/{task,concept,disorder,search}`; full JSON dump in GitHub `CognitiveAtlas/legacy_cogat_linkml/src/data/*.json` |
| HED 8.4.0 | event (time-locked) | Event / Agent / Action / Item / Property / Relation; Task-property subtrees | 1,233 tags | tag hierarchy (`is_a`) | `hed-standard/hed-schemas` |
| hed-task (2026) | canonical task + named variations | stimulus_modality / stimulus_kind / stimulus_role / response_modality / response_kind / instructions; inclusion_test{procedure, manipulations, measurements}; families; processes; references with roles | 103 tasks, 776 variations, 19 families, 172 processes, 486 task-process links | family membership (primary/secondary), variation-of, mappings to CogAt/CogPO | `hed-standard/hed-task/data/*.json, *.tsv`; site hedtags.org/hed-task |
| NIF/BIRNLex (NeuroLex/InterLex) | paradigm class | label, synonyms, acronym, editorial notes | ~30 paradigm classes | `subClassOf` (e.g., Sternberg ⊂ Item recognition) | `SciCrunch/NIF-Ontology/ttl/NIF-Investigation.ttl` |
| RDoC matrix | construct → list of paradigms | 8 "units of analysis" columns incl. Paradigms | free-text paradigm lists per (sub)construct | none (paradigm↔construct only) | NIMH web pages only (no API) |
| Experiment Factory / SRO (Sochat 2016; Eisenberg 2019) | runnable task implementation | `exp_id`, `cognitive_atlas_task_id`, `reference`, `time`, contributors | ~170 experiment folders; SRO battery = 37 tasks + 22 surveys, 129 task DVs | data-driven: 5 task factors (factor loadings) | GitHub `expfactory/expfactory-experiments`; `IanEisenberg/Self_Regulation_Ontology`; OSF `4j9hd` |
| BIDS | dataset task | `TaskName`, `TaskDescription`, `Instructions`, `CogAtlasID`, `CogPOID` (+ HED in events) | n/a | n/a | spec |
| NeuroVault | statistical map | `cognitive_paradigm_cogatlas(_id)`, `cognitive_contrast_cogatlas(_id)`, `contrast_definition(_cogatlas)`, `cognitive_paradigm_name/short_description/description_url` | uses CogAt | via CogAt | REST `neurovault.org/api/images/` |
| TaskExtractor (neurostore-text-extraction) | task mention in a paper | TaskName, TaskDescription, DesignDetails, Conditions, TaskMetrics, Concepts, Domain (10 CogAt classes), RestingState, TaskDesign, TaskDuration | 39k docs (local) | none (normalization is open) | `neurostuff/neurostore-text-extraction` |
| Psych-101 / Centaur (Binz et al. 2025) | whole experiment as natural-language transcript | `text`, `experiment` (author-year/exp path), `participant` | 160 experiments, 60,092 participants, 10.7M choices | ModernBERT prompt embeddings (MDS); domain labels | HF `marcelbinz/Psych-101` (Apache-2.0) |

---

## 1. CogPO: Cognitive Paradigm Ontology

**Citation:** Turner JA, Laird AR (2012). *The Cognitive Paradigm Ontology: design and application.* Neuroinformatics 10(1):57–66. [doi:10.1007/s12021-011-9126-x](https://doi.org/10.1007/s12021-011-9126-x) (PMID 21643732, PMC3682219). RRID:SCR_002235; homepage cogpo.org; [BioPortal COGPO](https://bioportal.bioontology.org/ontologies/COGPO) (199 classes, OWL, uploaded Dec 2010).

**Data:** `http://www.cogpo.org/ontologies/CogPOver1.owl` (HTTP 200, 210 KB, parsed for this report). The `CogPOver2010.owl` URL listed on BioPortal returns 404, and https on cogpo.org uses a self-signed cert. A copy also sits in the NIF-Ontology repo at `ttl/external/CogPO.ttl`.

**Design:**
- **Upper ontologies:** BFO upper level, OBI (`planned process`) and IAO (`action specification`).
- **Paradigm and conditions:** A *Behavioral Experimental Paradigm* (COGPO_00049, an OBI planned process) has ≥2 *Behavioral Experimental Paradigm Conditions* (COGPO_00109). Each condition must specify ≥1 stimulus, ≥1 instruction and ≥1 response.
- **Object properties (verbatim):**
  - `has_stimulus`: Condition → Stimulus. Subproperty of `ro:has_participant`.
  - `has_instructions`: Condition → Instructions.
  - `has_response_type` (COGPO_00006): Condition → Overt Response. Subproperty of `ro:has_part`.
  - `has_stimulus_modality` (COGPO_00011): Stimulus → Stimulus Modality. Subproperty of `bearer_of`.
  - `has_response_modality` (COGPO_00015): Overt Response → Response Modality.
- **Stimulus subtypes:** *Explicit* (experimenter-generated, external) vs *Implicit* (subject-generated, e.g., imagined content).
- **Response subtypes:** *Overt* vs *Covert*.
- **Worked example in the paper (FBIRN AudOdd):**
  - Condition "Standard Tones": Tones / Covert response / Attend.
  - Condition "Target Tones": Tones / Button Press / Discriminate.

### Full value lists (verbatim class labels from CogPOver1.owl)

**Stimulus Modality (COGPO_00124):** Auditory Modality; Gustatory Modality; Interoceptive Modality; Olfactory Modality; Tactile Modality, with subclasses Electrical modality, Pain Modality, Pressure Modality and Thermal Modality; Visual Modality. That is 6 top-level values plus 4 tactile subtypes.

**Stimulus Type: Explicit Stimulus (COGPO_00177), 41 values:** 3D Objects; Abstract Patterns; Acupuncture; Asian Characters; Braille Dots; Breathable Gas; Chord Sequences; Clicks; Digits; Electronic Stimulations; Eye Puffs; Faces; False Fonts; Film Clips; Fixation Point; Flashing Checkerboard; Food; Fractals; Heat; Infrared Laser; Infusion; Letters; Music; Noise; Nonverbal Vocal Sounds; Nonvocal Sounds; Odor; Pain; Pictures; Points of Light; Pseudowords; Random Dots; Reversed Speech; Shapes; Syllables; Symbols; TMS; Tactile Stimulation; Tones; Vibratory Stimulation; Words.
*Implicit Stimulus (COGPO_00178)* has no subclasses.

**Response Modality (COGPO_00119):** 8 FMA classes, with labels resolved through EBI OLS: FMA_24728 Face, with child FMA_49184 Mouth; FMA_24890 Arm; FMA_24979 Leg; FMA_25202 Shoulder; FMA_9578 Pelvis; FMA_9664 Foot; FMA_9712 Hand.

**Response Type: Response (COGPO_00175)**
- Covert Response (COGPO_00176)
- Overt Response (COGPO_00136), 17 values: Blink; Breath-Hold; Button Press; Draw; Drink; Extension; Finger Tapping; Grasp; Manipulate; Micturate; Point; Saccades; Smile Response; Speech; Swallow; Whistle; Write.

**Instructions (COGPO_00028, an IAO action specification), 17 values:** Attend; Count; Detect; Discriminate; Encode; Fixate; Generate; Imagine; Move; Name; Read; Recall; Repeat; Rest; Sing; Smile Instructions; Track.

**Behavioral Experimental Paradigm, 83 classes:** Action Observation; Acupuncture; Anti-Saccades; Braille Reading; Breath-Holding; Chewing or Swallowing; Classical Conditioning; Counting or Calculation; Cued Explicit Recognition; Deception Task; Deductive Reasoning; Delay Discounting Task; Delayed Non Match To Sample; Divided Auditory Attention; Drawing; Eating or Drinking; Encoding; Episodic Recall; Face Monitor or Discrimination; Film Viewing; Finger Tapping; Fixation; Flanker Task; Flashing Checkerboard; Flexion or Extension; Free Word List Recall; Go/No-Go; Grasping; Imagined Movement; Imagined Objects or Scenes; Isometric Force; Mental Rotation; Micturition Task; Music Comprehension or Production; Naming (Covert); Naming (Overt); Non-Painful Electrical Stimulation; Non-Painful Thermal Stimulation; **Oddball Discrimination**, with subclasses Auditory Oddball and Visual Oddball; Olfactory Monitor/Discrimination; Orthographic Discrimination; Pain Monitor/Discrimination; Paired Associate Recall; Passive Listening; Passive Viewing; Phonological Discrimination; Pitch Monitor/Discrimination; Pointing; Posner Task; Reading (Covert); Reading (Overt); Recitation/Repetition (Covert); Recitation/Repetition (Overt); Rest; Reward Task; Saccades; Semantic Monitor/Discrimination; Sequence Recall/Learning; Simon Task; Spatial/Location Discrimination; Sternberg Task; Stroop Task; Subjective Emotional Picture Discrimination; Syntactic Discrimination; Tactile Monitor/Discrimination; Task Switching; Theory of Mind Task; Tone Monitor/Discrimination; Transcranial Magnetic Stimulation; Vibrotactile Monitor/Discrimination; Video Games; Visual Distractor/Visual Attention; Visual Pursuit/Tracking; Whistling; Wisconsin Card Sorting Test; Word Generation (Covert); Word Generation (Overt); Word Stem Completion (Covert); Word Stem Completion (Overt); Writing; n-back. Every label in the OWL carries the suffix " Paradigm", for example "Flanker Task Paradigm".

**Relations between tasks:** Only `is_a`, and nearly flat: only Oddball has children. Variants are expressed compositionally, as the same paradigm class with different stimulus, response or instruction values per condition. No variant-of or family relation exists.

**Notes:**
- CogPO is frozen at the 2010 state of the BrainMap vocabulary. The live BrainMap lists below are larger: 115 paradigm classes, 68 stimulus types, 22 response types and 46 instructions.
- `hed-task` re-harvested CogPO (`data/cogpo_summary.json`) and extended the dimension vocabularies (Section 4).

---

## 2. BrainMap taxonomy

**Citations:**
- Fox PT, Laird AR, Fox SP, Fox PM, Uecker AM, Crank M, Koenig SF, Lancaster JL (2005). *BrainMap taxonomy of experimental design: description and evaluation.* Hum Brain Mapp 25(1):185–198. [doi:10.1002/hbm.20141](https://doi.org/10.1002/hbm.20141). This paper evaluated the taxonomy against filter choices in 46 published meta-analyses and found that no author-applied filter was absent from it.
- Fox PT, Lancaster JL (2002). *Mapping context and content: the BrainMap model.* Nat Rev Neurosci 3:319–321. [doi:10.1038/nrn789](https://doi.org/10.1038/nrn789).
- Laird AR, Lancaster JL, Fox PT (2005). *BrainMap: the social evolution of a human brain mapping database.* Neuroinformatics 3:65–78. [doi:10.1385/NI:3:1:065](https://doi.org/10.1385/NI:3:1:065).
- Lancaster JL et al. (2012). *Automated regional behavioral analysis for human brain images.* Front Neuroinform 6:23. [doi:10.3389/fninf.2012.00023](https://doi.org/10.3389/fninf.2012.00023). This is functional decoding over BD and PC.
- Live taxonomy: <https://brainmap.org/taxonomy/> (paradigms at `/taxonomy/paradigms/`, behavioral domains at `/taxonomy/behaviors/`).

**Unit of annotation:**
- **Experiment level (one contrast):** Context, Paradigm Class (multi-valued), Behavioral Domain (multi-valued).
- **Condition level:** Stimulus Modality, Stimulus Type, Stimulus Content, Stimulus Laterality, Response Modality, Response Type, Response Laterality, Instruction.
- **Subject and clinical metadata:** ICD codes (145 listed) and External Assessments (97 listed).
- **Database size (2012, from the CogPO paper):** 2,060 papers, 9,712 experiments. Yeo et al. 2015 used 10,449 experiments over 83 BrainMap "tasks", i.e., paradigm classes.

### Current controlled vocabularies (verbatim from brainmap.org/taxonomy, scraped 2026-10-09)

- **Context (12):** Aging | Disease | Emotion | Experimental Design | Gender | Genetic | Handedness | Language | Learning | Normal Mapping | Pharmacology | Treatment
- **Stimulus Modality (7):** Auditory | Gustatory | Interoceptive | Olfactory | Other | Tactile | Visual
- **Stimulus Type (68):** 3D Objects | Abstract Patterns | Abstract/Geometrical | Acupuncture | Air Puff | Animations | Arrow | Asian Characters | Braille | Cartoons | Clicks | Cold | Digits | Dots | Electricity | Faces | Faces and Scenes | False Font | Film Clip | Fixation Point | Flashing Checkerboard | Food | Fractals | Heartbeat | Heat | Images | Infusion | Inhalation | Instruction | Letters | Lights | Lines | Mathematical Equation | Music | Noise | Nonverbal Vocal Sounds | Nonvocal Sounds | Number | Numbers | Objects | Odor | Pain | Pictures | Pressure | Pseudowords | Reversed Speech | Scenes | Sentences | Shapes | Short Sentences | Sketches | Sounds (Environmental) | Spinner | Stories | Syllables | Symbols | Tactile Stimulation | Target | Thermal stimulation | Tones | Uniform Screen | Vibration | Vibratory Stimulation | Video | Videogame | Vignettes | Vocal Sounds | Words
- **Stimulus Content (17):** Action (bodily) | Category (semantic) | Color | Congruence | Emotion | Emotion (negative) | Emotion (positive) | Morphology (word) | Motion (object) | Neutral | Pain | Pleasure | Reward | Semantics | Shape (visual) | Somatotopy | Syntax
- **Stimulus Laterality (5):** Bilateral | Left | Midline | Right | Varying
- **Response Modality (10):** Arm | Foot | Hand | Leg | Ocular | Oral/Facial | Other | Pelvis | Shoulder | Torso
- **Response Type (22):** Blink | Breath-Hold | Button Press | Draw | Drink | Finger Tapping | Flexion/Extension | Grasp | Imagine | Inhale | Manipulate | Meditate | Micturate | Point | Press | Read | Saccades | Smile | Speech | Swallow | Whistle | Write
- **Response Laterality (6):** Bilateral | Left | Midline | Not Applicable | Right | Varying
- **Instruction (46):** Add | Answer | Anticipate | Attend | Choose | Compare | Count | Describe | Detect | Discriminate | Encode | Exhale | Experience | Fixate | Generate | Identify | Imagine | Indicate | Inhale | Inhibit | Learn | Listen | Look | Maintain | Meditate | Move | Name | Passive/Rest | Perform | Predict | Press | Rate | Read | Recall | Repeat | Report | Saccade | Sing | Swallow | Tap | Think | Touch | Track | Update | View | Write

**Behavioral Domain (5 domains, 3 levels; definitions on the site):**
- **Action:** Execution (Unspecified, Speech) · Imagination · Inhibition · Motor Learning · Observation · Preparation
- **Cognition:** Attention · Language (Unspecified, Orthography, Phonology, Semantics, Speech, Syntax) · Memory (Unspecified, Explicit, Implicit, Working) · Music · Reasoning · Social Cognition · Somatic · Spatial · Temporal
- **Emotion:** Intensity · Valence · Negative (Unspecified, Anger, Anxiety, Disgust, Embarrassment, Fear, Guilt, Punishment/Loss, Sadness) · Positive (Unspecified, Happiness, Humor, Reward/Gain)
- **Interoception:** Baroregulation · Gastrointestinal/Genitourinary (GI/GU) · Heartbeat Detection · Hunger · Osmoregulation · Respiration Regulation · Sexuality · Sleep · Thermoregulation · Thirst · Vestibular
- **Perception:** Audition · Gustation · Olfaction · Somesthesis (Unspecified, Pain) · Vision (Unspecified, Color, Motion, Shape)

**Paradigm Class (115):** The full list, with BrainMap's verbatim definition and its **"First:" (origin) and "Most:" citations**, is in Appendix A. This is the only resource found that attaches an origin citation to each paradigm class, so it seeds a provenance facet directly.

**Relations between tasks:** Paradigm classes are flat; there is no is-a between them. Variants are expressed as separate sibling classes, for example Stroop-Color / -Counting / -Emotional / -Spatial / -Other and the five Magnitude Comparison classes, or as covert/overt pairs. Families can only be inferred from naming or from shared BD/stimulus/response codes.

**Data-driven relations built on BrainMap:**
- Yeo et al. 2015 (Cereb Cortex 25:3654–72, [doi:10.1093/cercor/bhu217](https://doi.org/10.1093/cercor/bhu217)) fit an author-topic-style hierarchical Bayesian model: task → cognitive components → voxels, on 10,449 experiments × 83 paradigm classes. It yields Pr(component | task) vectors, giving a 12-component task embedding with a nested hierarchy.
- Laird et al. 2015, *Neural architecture underlying classification of face perception paradigms*, NeuroImage 119:70–80 ([doi:10.1016/j.neuroimage.2015.06.044](https://doi.org/10.1016/j.neuroimage.2015.06.044)), clustered BrainMap face experiments into 4 paradigm subclasses based on their activation patterns.

**Automated annotation with this vocabulary:**
- Turner MD, Chakrabarti C, Jones TB, Xu JF, Fox PT, Luger GF, Laird AR, Turner JA (2013). *Automated annotation of functional imaging experiments via multi-label classification.* Front Neurosci 7:240. [doi:10.3389/fnins.2013.00240](https://doi.org/10.3389/fnins.2013.00240).
  - **Corpus:** 247 PubMed abstracts (psychiatric studies) with BrainMap expert labels.
  - **Labels per dimension:** Behavioral domain 40, Paradigm class 48, Instruction 14, Response modality 5, Response type 9, Stimulus modality 5, Stimulus type 17.
  - **Methods:** NB/kNN/SMO with binary-relevance and label-powerset transforms.
  - **Best exact match:** 78% (stimulus modality); paradigm class 43%; stimulus type 33%.
  - **Best F1-micro:** stimulus modality 0.84; paradigm class 0.46.
  - **Takeaway:** fine-grained stimulus and paradigm labels are hard to recover from abstracts alone.
- Chakrabarti, Luger, Laird, Turner (c. 2012) did earlier text mining on BrainMap abstracts and reported performance only somewhat better than chance ([PDF](https://www.cs.unm.edu/~luger/resumepapers2015/2012%20papers/ChakLugLairdTurner.pdf)).
- Annotations are available only under a BrainMap Collaborative Use License Agreement.

---

## 3. Cognitive Atlas: tasks

**Citations:**
- Poldrack RA, Kittur A, Kalar D, Miller E, Seppa C, Gil Y, Parker DS, Sabb FW, Bilder RM (2011). *The Cognitive Atlas: toward a knowledge foundation for cognitive neuroscience.* Front Neuroinform 5:17. [doi:10.3389/fninf.2011.00017](https://doi.org/10.3389/fninf.2011.00017).
- Precursor: Lenartowicz A, Kalar DJ, Congdon E, Poldrack RA (2010). *Towards an ontology of cognitive control.* Top Cogn Sci 2:678–692. [doi:10.1111/j.1756-8765.2010.01100.x](https://doi.org/10.1111/j.1756-8765.2010.01100.x).

**Size (live site, 2026-10-09):** 857 tasks, 918 concepts, 242 phenotypes, 44 collections.

### Task schema

Taken from the API record keys and the LinkML schema `legacy_cogat_linkml.yaml`:
- **Task** (`is_a CitableThing`): `id` (`tsk_…` or `trm_…`), `name`, `alias` (comma-separated string), `definition_text`, `id_concept_class`, `has_condition`, `has_contrast`, `has_indicator`, `asserts`, `in_battery`, `has_implementation`, `has_external_dataset`, `has_citation`, `kind_of`, `part_of`, `review_status`, plus provenance fields (`id_user`, `def_id_user`, `event_stamp`, `creation_time`, `last_updated`).
- **Condition:** `name`, `condition_text`, `condition_description`. The site defines conditions as "the subsets of an experiment that define the relevant experimental manipulation".
- **Contrast:** `name`, `has_difference`, plus the conditions involved. The site defines a contrast as "any function over experimental conditions. The simplest contrast is the indicator value for a specific condition; more complex contrasts include linear or nonlinear functions…".
- **Indicator:** `type`, a free text value. The site defines it as "a specific quantitative or qualitative variable that is recorded for analysis… behavioral … or physiological variables".
  - The vocabulary is not controlled: 226 distinct strings over 236 indicator nodes.
  - Most common values: accuracy (145 tasks), response time (94), areas of activation (28), ERP (11), BOLD activity (9), reaction time (8), Stop Signal Reaction Time.
- **Implementation:** `implementation_name`, `implementation_uri`, `implementation_description`. Example: STOP-IT, Cognition Lab SST.
- **ExternalDataset:** `dataset_name`, `dataset_uri`. Examples: OpenfMRI ds000007, NeuroVault collections.
- **Battery** (collection): `name`, `collection_alias`, `collection_publisher`, `collection_description`. There are 37 batteries, including WAIS-IV, WMS-IV, CANTAB, NIH Toolbox (and its Cognition, Emotion, Motor and Sensation sub-batteries), Penn CNB/WebCNP, NCANDA, ADNI-1, ADAScog, HCP 500 tfMRI and "Self regulation tasks".
- **Citation:** `citation_pmid`, `citation_authors`, `citation_pubdate`, `citation_pubname`, `citation_desc`, `citation_type`, `doi`. This is a bibliography, not a typed role: the dump does not distinguish origin citations from usage citations.
- **Assertion:** a reified triple with `subject` (concept), `predicate` (task), `predicate_def` (contrast), `truth_value`, `confidence_level`, `in_theory`. Example: "response inhibition is measured by the contrast of Stop Signal Reaction Time trials in the stop signal task".
- **Concept classes (`ctp_C1…C10`):** Perception; Attention; Reasoning and Decision Making; Executive/Cognitive Control; Learning and Memory; Language; Action; Emotion; Social Function; Motivation.
  - **Note:** TaskExtractor's `Domain` enum uses exactly these 10 Cognitive Atlas classes, not BrainMap's 5 behavioral domains. JOURNAL.md calls them BrainMap domains; that is a mislabel.

**Coverage counts** (853 tasks in the 2025-02-19 Neo4j dump):

| Field | Tasks with it | Total items |
|---|---|---|
| has_contrast | 529 | 1,585 contrasts |
| asserts (concept links) | 477 | 1,237 |
| has_citation | 470 | |
| has_indicator | 317 | |
| has_condition | 272 | 807 conditions |
| in_battery | 113 | |
| has_external_dataset | 66 | |
| has_implementation | 55 | |
| kind_of | 54 | 67 edges |
| part_of | 42 | 51 edges |

### Task–task relations

`kind_of` and `part_of` exist at the data level. Both are sparse and their direction is inconsistent.

**Sensible `kind_of` edges:**
- color-word Stroop → Stroop task
- chimeric animal Stroop → Stroop task
- AX-CPT → Continuous Performance Task
- forward digit span → digit span
- backward digit span → digit span
- incentive modulated antisaccade → antisaccade/prosaccade

**Wrong or inverted edges:**
- n-back task `kind_of` Penn CPT
- word stem completion (overt) `kind_of` word stem completion (covert)
- naming (overt) `part_of` naming (covert)
- face n-back `part_of` n-back / spatial n-back / letter n-back

Many BrainMap paradigm classes were imported as CogAt tasks with lowercase names, such as "tone monitor/discrimination" and "cued explicit recognition". Use these relations only as weak hints.

**Task → concept ("measures"):** `ASSERTS` edges carry the contrast through which the concept is measured. The web page renders this as "<task> has been asserted to measure the following CONCEPTS … as measured by the contrast: …". Concepts have their own `kind_of`/`part_of` hierarchy.

### API and data access

- **REST:** `https://www.cognitiveatlas.org/api/v-alpha/task` (list, 857 records), `…/task?id=tsk_…` (full record with conditions, contrasts, concepts, indicators, implementations, citations, batteries, disorders, external_datasets), `…/concept`, `…/disorder`, `…/search?q=`. The API page lists the same endpoints under `/api/{concept,task,disorder,search}`.
- **Python:** `cognitiveatlas` (cogat-python, GET only). NiMARE `annotate.cogat.extract_cogat` does regex alias matching, and `expand_counts` propagates counts along isKindOf/isPartOf/inCategory.
- **Bulk:** <https://github.com/CognitiveAtlas/legacy_cogat_linkml> → `src/data/{Task,Concept,Condition,Contrast,Indicator,Assertion,Battery,Citation,Implementation,ExternalDataset,Disorder,Trait,Behavior,Theory}Collection.json`, plus the LinkML schema. Older OWL export: `SciCrunch/NIF-Ontology/ttl/external/cogat_v0.3.owl`.

---

## 4. HED and hed-task (brief; covered in depth by another agent)

**HED standard schema**
- Robbins K, Truong D, Appelhoff S, Delorme A, Makeig S (2021). *Capturing the nature of events and event context using hierarchical event descriptors (HED).* NeuroImage 245:118766. [doi:10.1016/j.neuroimage.2021.118766](https://doi.org/10.1016/j.neuroimage.2021.118766).
- Schema 8.4.0 (`hed-standard/hed-schemas/standard_schema/hedtsv/HED8.4.0/HED8.4.0_Tag.tsv`) has 1,233 tags under 6 roots: **Event, Agent, Action, Item, Property, Relation**. Task-relevant subtrees (verbatim):

| Subtree | Values |
|---|---|
| Event | Sensory-event, Agent-action, Data-feature, Experiment-control, Experiment-procedure, Experiment-structure, Measurement-event |
| Property/Task-property/Task-event-role | Cue, Experimental-stimulus, Feedback, Incidental, Instructional, Mishap, Participant-response, Task-activity, Warning |
| Task-stimulus-role | Distractor, Expected, Extraneous, Go-signal, Meaningful, Newly-learned, Non-informative, Non-target, Not-meaningful, Novel, Oddball, Penalty, Planned, Priming, Query, Reward, Stop-signal, Target, Threat, Timed, Unexpected, Unplanned |
| Task-action-type | Appropriate-action, Correct-action, Correction, Done-indication, Imagined-action, Inappropriate-action, Incorrect-action, Indeterminate-action, Miss, Near-miss, Omitted-action, Ready-indication |
| Task-attentional-demand | Bottom-up-attention, Covert-attention, Divided-attention, Focused-attention, Orienting-attention, Overt-attention, Selective-attention, Sustained-attention, Switched-attention, Top-down-attention |
| Task-effect-evidence | Behavioral-evidence, Computational-evidence, External-evidence, Intended-effect |
| Task-relationship | Background-subtask, Primary-subtask |
| Sensory-presentation | Auditory- (Loudspeaker-separation, Monophonic, Silent, Stereophonic), Gustatory-, Olfactory-, Somatic-, Tactile-, Vestibular-, Visual-presentation (2D-view, 3D-view, Background-view, Bistable-view, Foreground-view, Foveal-view, Map-view, Peripheral-view) |
| Action/Think | Allow, Attend-to, Count, Deny, Detect, Discriminate, Encode, Evade, Generate, Identify, Imagine, Judge, Learn, Memorize, Plan, Predict, Recall, Recognize, Respond, Switch-attention, Track |
| Action/Perceive | Hear, See, Sense-by-touch, Smell, Taste |
| Action/Perform | Close, Collide-with, Halt, Modify, Open, Operate, Play, Read, Repeat, Rest, Ride, Write |
| Item/Language-item | Character, Clause, Glyph, Nonword, Paragraph, Phoneme, Phrase, Pseudoword, Sentence, Syllable, Textblock, Word |
| Organizational-property | Condition-variable, Control-variable, Indicator-variable, Experimental-trial, Experimental-intertrial, Task, Time-block, Def/Definition, … |
| Move-body-part / Communicate | Move-eyes (Blink, Fixate, Saccade…), Move-upper-extremity (Grasp, Point, Press, Reach…), Communicate-vocally (Speak, Whisper…), Communicate-musically (Sing, Whistle…), Communicate-gesturally (Smile, Nod-head…) |

- HED's `Condition-variable` and `Indicator-variable` mirror Cognitive Atlas "conditions" and "indicators".
- Library schemas: `score`, `lang`, `slam`, `mouse`.

**hed-task**, <https://github.com/hed-standard/hed-task> (site hedtags.org/hed-task; created 2026-04, active)
- **Coverage:** 103 tasks (+4 pseudo-tasks), 776 named variations, 19 families, 172 cognitive processes in 19 categories, 486 task–process links, with mappings to CogAt tasks and concepts and to CogPO paradigms.
- **Task record:** `hedtsk_id`, `canonical_name`, `task_kind` {task, pseudo_task}, `aliases`, `short_definition`, `description`, `inclusion_test{procedure[], manipulations[], measurements[]}`, `variations[{name, description, justification, variation_id}]`, `families[{family_id, role∈{primary, secondary}, confidence∈{high, review}, rationale}]`, `hed_process_ids`, `references[{roles, title, authors, year, journal, ids{doi, openalex_id, pmid, pmcid, s2_id, arxiv_id}, …}]`.
- **Reference role vocabulary:** historical | review | experiment | dataset | other | unknown. "historical" is the origin-citation role.
- **Families (19):** conflict_and_interference, response_inhibition, attentional_cueing, visual_search_and_tracking, oddball_and_vigilance, perceptual_judgment, working_memory_span, recall_and_recognition, memory_control, metacognition_and_interoception, conditioning_and_reinforcement, motor_performance, executive_and_reasoning, reward_and_value_choice, social_cognition_and_games, emotion, language, spatial_navigation, pseudo_tasks.
- **Facet vocabularies** (`data/facet_defs.tsv`), CogPO-derived and extended:
  - stimulus_modality (10)
  - stimulus_kind (46): the CogPO 41 + sentences, scenes, monetary_amounts, playing_cards, virtual_environment
  - stimulus_role (12): target, non_target, feedback, reward, distractor, cue, oddball, penalty, go_signal, stop_signal, prime, novel
  - response_modality (11): CogPO 8 + eye, torso, finger
  - response_kind (23): CogPO 17 + breathe, key_press, mouse_click, touchscreen_tap, rating, no_response
  - instructions (32)

---

## 5. Other schemas, batteries and registries

### Experiment Factory and the Self-Regulation Ontology
- **Experiment Factory paper:** Sochat VV, Eisenberg IW, Enkavi AZ, Li J, Bissett PG, Poldrack RA (2016). *The Experiment Factory: standardizing behavioral experiments.* Front Psychol 7:610. [doi:10.3389/fpsyg.2016.00610](https://doi.org/10.3389/fpsyg.2016.00610).
- **Repo:** `expfactory/expfactory-experiments` has about 170 experiment folders, including many dual-task combinations such as `stop_signal_with_n_back` and `go_nogo_with_flanker`, and `__fmri` / `__practice` variants.
  - Each `config.json` carries `exp_id`, `name`, `template`, **`cognitive_atlas_task_id`** (for example stroop → `tsk_4a57abb949e27`), `reference` (a URL to the source paper), `contributors`, `time` (minutes), `notes`, and `experiment_variables`.
  - This is a clean example of implementation → CogAt task → reference linkage. Variant naming is compositional (`<task>_with_<task>`, `__<context>`).
- **Self-Regulation Ontology:** Eisenberg IW, Bissett PG, Enkavi AZ, Li J, MacKinnon DP, Marsch LA, Poldrack RA (2019). *Uncovering the structure of self-regulation through data-driven ontology discovery.* Nat Commun 10:2319. [doi:10.1038/s41467-019-10301-1](https://doi.org/10.1038/s41467-019-10301-1).
  - Reliability companion: Enkavi et al. 2019 PNAS 116:5472. [doi:10.1073/pnas.1818430116](https://doi.org/10.1073/pnas.1818430116).
  - **Sample and measures:** 522 MTurk participants (150 retest), 37 tasks + 22 surveys, 193 DVs (129 task).
  - **Task factors (5):** Speeded Information Processing, Caution, Perception/Response, Strategic Information Processing, and a discounting factor. There are 12 survey factors.
  - **Battery tasks** (task prefixes in `Data/Complete_02-16-2019/meaningful_variables.csv`): adaptive_n_back, angling_risk_task_always_sunny, attention_network_task, bickel_titrator, choice_reaction_time, cognitive_reflection, columbia_card_task_cold/hot, dietary_decision, digit_span, directed_forgetting, discount_titrate, dot_pattern_expectancy, go_nogo, hierarchical_rule, holt_laury, information_sampling_task, keep_track, kirby, local_global_letter, motor_selective_stop_signal, probabilistic_selection, psychological_refractory_period_two_choices, ravens, recent_probes, shape_matching, shift_task, simon, simple_reaction_time, spatial_span, stim_selective_stop_signal, stop_signal, stroop, threebytwo, tower_of_london, two_stage_decision, writing_task.
  - **Data:** GitHub `IanEisenberg/Self_Regulation_Ontology` (trial-level data), OSF <https://osf.io/4j9hd/>.
  - This gives a **behavioral, data-driven task-relatedness** measure: task DV loadings on latent factors.

### NIH Toolbox
- **Citation:** Weintraub S et al. (2013). *Cognition assessment using the NIH Toolbox.* Neurology 80(11 Suppl 3):S54–64. [doi:10.1212/WNL.0b013e3182872ded](https://doi.org/10.1212/WNL.0b013e3182872ded).
- **Domains:** Cognition, Emotion, Motor, Sensation.
- **Cognition battery:** Dimensional Change Card Sort, Flanker Inhibitory Control & Attention, Picture Sequence Memory, List Sorting Working Memory, Pattern Comparison Processing Speed, Picture Vocabulary, Oral Reading Recognition, plus supplemental Rey Auditory Verbal Learning and Oral Symbol Digit *(test list not re-verified)*.
- Cognitive Atlas encodes the Toolbox as batteries, but its Cognition battery entry lists only 6 tests (Flanker and Pattern Comparison are missing). It is a proprietary, normed instrument, not a vocabulary.

### RDoC
- **Matrix:** NIMH RDoC matrix (<https://www.nimh.nih.gov/research/research-funded-by-nimh/rdoc/constructs/rdoc-matrix>).
  - Domains (now 6): Negative Valence, Positive Valence, Cognitive Systems, Social Processes, Arousal and Regulatory Systems, Sensorimotor Systems.
  - Columns: Genes, Molecules, Cells, Circuits, Physiology, Behavior, Self-Report, **Paradigms**.
- **Paradigms** are free-text lists per (sub)construct. Example, Working Memory / Active Maintenance (verbatim): AX-CPT/DPX; Change detection tasks; Complex Span tasks; delayed match to non sample; delayed match to sample; keep track task; Letter memory/running memory; Letter Number Sequencing; N-back; Self-Ordered Pointing; sequence encoding and reproduction; Simple Span Tasks; Sternberg Item Recognition.
- There are no IDs, no API and no task–task relations. The construct→paradigm "measures" mapping is useful, but needs scraping.

### NeuroLex / NIFSTD / BIRNLex / InterLex
- **Citations:**
  - Bug WJ et al. (2008). *The NIFSTD and BIRNLex vocabularies.* Neuroinformatics 6:175–194. [doi:10.1007/s12021-008-9032-z](https://doi.org/10.1007/s12021-008-9032-z).
  - Larson SD, Martone ME (2013). *NeuroLex.* Front Neuroinform 7:18. [doi:10.3389/fninf.2013.00018](https://doi.org/10.3389/fninf.2013.00018).
- **Content:** `ttl/NIF-Investigation.ttl` has about 30 paradigm or test classes under "Behavioral paradigm" / "Experimental paradigm", with BIRNLEX IDs, synonyms, acronyms and editorial notes.
- **Verbatim labels:** Action observation; Acupuncture; Anti saccade; Auditory oddball; Breathhold; Classical conditioning; Covert braille reading; Covert visual reading; Deductive reasoning; Delayed matching to sample; Divided auditory attention; Drawing; Eating; Encoding; Episodic recall; Eye Saccade; Fear conditioning; Item recognition; Mismatch negativity; Oddball discrimination; Reading; Sensorimotor; Serial item recognition; Simple saccade; Sternberg; Visual oddball (all "... paradigm"); plus California Verbal Learning Test, North American Adult Reading Test, Reaction time test, Trail making test.
- **Relations:** real `subClassOf` edges, for example Sternberg paradigm ⊂ Item recognition paradigm. The editorial note there reads "Brain Map uses this designation only when letters are used as stimuli".
- Small and BrainMap-derived. InterLex includes these terms.

### OntoNeuroLOG
- **Citation:** Batrancourt B, Dojat M, Gibaud B, Kassel G (2015). *A multilayer ontology of instruments for neurological, behavioral and cognitive assessments.* Neuroinformatics 13(1):93–110. [doi:10.1007/s12021-014-9244-3](https://doi.org/10.1007/s12021-014-9244-3).
- **Design:** DOLCE-based. A core ontology of *instruments* (artefacts, their variables, scores and the actions performed with them) plus domain ontologies for specific neuropsychological, behavioral and neuroclinical tests. BioPortal module `ONL-MSA`.
- **Relevance:** a good model for "instrument / score / variable" (the measures facet). It is not a paradigm vocabulary.

### NIDM and NeuroVault
- **NIDM-Results:** Maumet C et al. (2016). Sci Data 3:160102 *(not re-verified)*. Encodes contrasts and statistic maps.
- **NIDM-Experiment:** Keator et al. 2013 *(not re-verified)*. Encodes acquisition. Task identity is carried by BIDS `TaskName` and CogAt links rather than by a native task vocabulary.
- **NeuroVault** image records (API verified) carry `cognitive_paradigm_cogatlas`, `cognitive_paradigm_cogatlas_id`, `cognitive_contrast_cogatlas`, `cognitive_contrast_cogatlas_id`, `contrast_definition`, `contrast_definition_cogatlas`, `cognitive_paradigm_name`, `cognitive_paradigm_short_description` and `cognitive_paradigm_description_url`.
- NeuroVault is the largest real-world use of CogAt task/contrast IDs. `vsoch/decoding` and `vsoch/semantic-image-comparison-web` used these for concept decoding.

### BIDS
- **Citation:** Gorgolewski KJ et al. (2016). Sci Data 3:160044. [doi:10.1038/sdata.2016.44](https://doi.org/10.1038/sdata.2016.44).
- **Task metadata** (`*_bold.json`, `*_beh.json`, `*_events.json`), all RECOMMENDED strings:
  - `TaskName`: unique per dataset; the `task-<label>` entity is derived by stripping non-alphanumerics.
  - `TaskDescription`
  - `Instructions`: "Text of the instructions given to participants before the recording".
  - `CogAtlasID`: "URI of the corresponding Cognitive Atlas Task term".
  - `CogPOID`: "URI of the corresponding CogPO term".
- **Events:** `events.tsv` columns (`trial_type`, extra columns documented in the sidecar) plus optional `HED`.

### Other ontologies, mentioned for completeness *(not re-verified)*
- Mental Functioning Ontology (Hastings et al. 2012)
- NEMO (ERP ontology; Frishkoff/Dou et al.), which includes ERP paradigm terms
- OBI `assay` / `planned process`, which CogPO already imports

---

## 6. Data-driven task collections and automatic extraction

### Psych-101 / Centaur
- **Citation:** Binz M, … Schulz E (2025). *A foundation model to predict and capture human cognition.* Nature 644. [doi:10.1038/s41586-025-09215-4](https://doi.org/10.1038/s41586-025-09215-4); arXiv 2410.20268.
- **Scale:** 160 experiments, 60,092 participants, 10,681,650 choices, 253.6M tokens.
- **Format:** Each experiment was hand-transcribed into natural language: instructions follow the original wording, the full trial history is included, and responses are marked `<<…>>`.
- **Domains** (Fig. 1): multi-armed bandits, decision-making, memory, supervised learning, Markov decision processes, other.
- **Data:** HF `marcelbinz/Psych-101` (fields `text`, `experiment`, `participant`; Apache-2.0); gated test set `marcelbinz/Psych-101-test`; code at `github.com/marcelbinz/Llama-3.1-Centaur-70B`; successor `github.com/marcelbinz/Psych-201`.
  - Psych-201 (arXiv 2605.07632): 208,021 participants, 25.9M responses.
- **Task similarity:** Experiments were embedded with ModernBERT on the prompt up to the first choice and projected with MDS (Supplementary Fig. 8). Behavioral similarity used 10 CogBench metrics (Fig. 4a).
- The `experiment` key (author-year/exp) is in effect a provenance ID. There is no task-type vocabulary.

### Neurosynth and NeuroQuery (term-based, no task entity)
- **Neurosynth:** Yarkoni T, Poldrack RA, Nichols TE, Van Essen DC, Wager TD (2011). Nat Methods 8:665–670. [doi:10.1038/nmeth.1635](https://doi.org/10.1038/nmeth.1635). Abstract n-gram TF-IDF features plus LDA topic sets.
  - Task names such as "n-back", "stroop" and "go nogo" appear as ordinary terms mixed with constructs.
  - Data: `neurosynth/neurosynth-data` *(not re-verified)*.
- **Topic mapping:** Poldrack RA et al. (2012). *Discovering relations between mind, brain, and mental disorders using topic mapping.* PLoS Comput Biol 8:e1002707. [doi:10.1371/journal.pcbi.1002707](https://doi.org/10.1371/journal.pcbi.1002707).
- **NeuroQuery:** Dockès J et al. (2020). eLife 9:e53385. [doi:10.7554/eLife.53385](https://doi.org/10.7554/eLife.53385). 7,547 terms × 13,459 publications. Its vocabulary mixes Cognitive Atlas, MeSH and other sources, task names included.
- **Beam et al. (2021):** *A data-driven framework for mapping domains of human neurobiology.* Nat Neurosci 24:1733–1744. [doi:10.1038/s41593-021-00948-9](https://doi.org/10.1038/s41593-021-00948-9). Text-mined about 18k fMRI papers, clustered 1,600+ function terms into domains, and compared them with RDoC and DSM.

### Neurosynth Compose / NeuroStore and TaskExtractor
- **Citation:** Kent JD, Lee N, Laird AR, Salo T, Peraza J, Bottenhorn KL, Oudyk K, Nichols TE, Poline J-B, de la Vega A (2026). *Neurosynth Compose: a web-based platform for flexible and reproducible neuroimaging meta-analysis.* Imaging Neuroscience 4. [doi:10.1162/IMAG.a.1114](https://doi.org/10.1162/IMAG.a.1114).
- **TaskExtractor** (`neurostuff/neurostore-text-extraction/ns_extract/pipelines/nv_task/schemas.py`) is an LLM structured-output schema:
  - Study level: `Modality` (fMRI-BOLD, StructuralMRI, DiffusionMRI, PET FDG, PET [15O]-water, fMRI-CBF, fMRI-CBV, MEG, EEG, Other), `StudyObjective`, `Exclude` (MetaAnalysis | Review).
  - Per task: `TaskName`, `TaskDescription`, `DesignDetails`, `Conditions[]`, `TaskMetrics[]`, `Concepts[]`, `Domain[]` (the 10 Cognitive Atlas concept classes).
  - fMRI tasks add `RestingState`, `RestingStateMetadata`, `TaskDesign` (Blocked | EventRelated | Mixed | Other) and `TaskDuration`.
  - NiMARE already uses `TaskExtractor.fMRITasks[0].RestingState` as an annotation target.
- **Gap:** no stimulus, response or instruction facets, and no normalization to IDs.
- **NiCLIP:** Peraza JA, Kent JD, Nichols TE, Poline J-B, de la Vega A, Laird AR (2025). bioRxiv [doi:10.1101/2025.06.14.659706](https://doi.org/10.1101/2025.06.14.659706). A CLIP model over about 23k articles that predicts tasks, concepts and domains from maps. It reports better results with "a curated cognitive ontology with precise task-concept-domain mappings" and with full text rather than abstracts.

### LLM metadata extraction
- **Citation:** Turner MD, Appaji A, Ar Rakib N, Golnari P, Rajasekar AK, Rathnam KV A, Sahoo SS, Wang Y, Wang L, Turner JA (2025). *Large language models can extract metadata for annotation of human neuroimaging publications.* Front Neuroinform 19:1609077. [doi:10.3389/fninf.2025.1609077](https://doi.org/10.3389/fninf.2025.1609077).
- **Results:** GPT-4o reached 0.91–0.97 agreement with human annotators on imaging type (T1 / resting / task), 12 sMRI parameters, and diagnosis × group size (NeuroBridge ontology).
- It does **not** extract paradigm classes. Code: `github.com/NeuroBridge/LLM-Metadata-Extraction-Paper-2025`.
- **Gap:** No published LLM study was found that extracts tasks and normalizes them to CogAt/CogPO/BrainMap IDs with an evaluation. The closest prior baseline remains Turner et al. 2013 (CogPO from abstracts).

### Text- and embedding-based task–construct linking
- **CogText:** Ansarinia M, Schrater P, Cardoso-Leite P (2022). *Linking theories and methods in cognitive sciences via joint embedding of the scientific literature: the example of cognitive control.* CogSci 2022; arXiv [2203.11016](https://arxiv.org/abs/2203.11016).
  - Lexicon of 172 terms (72 task names, 100 constructs) drawn from cognitive control, executive function and self-regulation sources, including Enkavi 2019.
  - One PubMed query per term retrieved 385,705 unique abstracts.
  - Embeddings: GPT-3 Ada (1024-d). The task–construct graph embedding uses constrained random walks, and inter-task distance is measured by Jensen-Shannon divergence, for example Trail Making ≈ Digit Span.
  - It can generate task batteries for a given set of constructs.
- **Sochat tooling:** `word-fish/wordfish-python` (term and relationship extraction over standardized vocabularies), `vsoch/nsynth2ca` (Neurosynth terms → CogAt), `vsoch/william_james` (CogAt term finding).

---

## 7. Task similarity and relatedness measures

| Approach | Signal | Example | Reuse |
|---|---|---|---|
| Shared ontology annotations | Jaccard/cosine over CogPO/BrainMap facet values or CogAt concepts | BrainMap behavioral profiles (Lancaster 2012); Turner & Laird 2012 argue that categorizing by stimulus/response/instruction allows retrieval "across multiple paradigm levels" | facet overlap gives an interpretable distance |
| Concept co-assertion | tasks linked to the same CogAt concepts | Poldrack & Yarkoni 2016, *From brain maps to cognitive ontologies*, Annu Rev Psychol 67:587–612, [doi:10.1146/annurev-psych-122414-033729](https://doi.org/10.1146/annurev-psych-122414-033729); Lenartowicz 2010 | bipartite task–concept graph |
| Latent-component models of activation | Pr(component \| task) | Yeo 2015 (83 BrainMap tasks, 12 components); Laird 2015 face-paradigm clustering | a neural task embedding |
| Encoding models over large task batteries | voxel weights per task; metadata features | Nakai & Nishimoto 2020, Nat Commun 11:1142, [doi:10.1038/s41467-020-14913-w](https://doi.org/10.1038/s41467-020-14913-w): 103 tasks, sparse task-type model gives a task hierarchy; cognitive-factor model uses Neurosynth-derived features to decode novel tasks. King et al. 2019, Nat Neurosci 22:1371, [doi:10.1038/s41593-019-0436-x](https://doi.org/10.1038/s41593-019-0436-x): MDTB, 26 tasks / 47 conditions | task × feature matrices |
| Multi-task fMRI atlases annotated with ontologies | contrasts labeled with CogAt concepts | Varoquaux et al. 2018, PLoS Comput Biol 14:e1006565, [doi:10.1371/journal.pcbi.1006565](https://doi.org/10.1371/journal.pcbi.1006565): 30 studies / 196 conditions. IBC: Pinho et al. 2018 Sci Data 5:180105, [doi:10.1038/sdata.2018.105](https://doi.org/10.1038/sdata.2018.105); 2020 [doi:10.1038/s41597-020-00670-4](https://doi.org/10.1038/s41597-020-00670-4); now 67 tasks / 530 contrasts / 188 concepts per EBRAINS | gold task→contrast→concept annotations |
| Individual-differences factor structure | correlation of task DVs across people | Eisenberg 2019 (5 task factors); Enkavi 2019 | a behavioral task space |
| Transfer-learning "cognitive taskonomy" | decoder transfer between task states | arXiv 2206.03950; 2407.00033 (23 HCP task states); 2606.26279 | — |
| Shared-network task representations | RNN unit clustering over 20 tasks; compositional instructions | Yang et al. 2019, Nat Neurosci 22:297, [doi:10.1038/s41593-018-0310-2](https://doi.org/10.1038/s41593-018-0310-2) | conceptual model of task composition |
| Text embeddings of task descriptions | LM embeddings of abstracts or prompts | CogText (Ansarinia 2022); Centaur ModernBERT prompt embeddings | directly applicable to our 20k task-name long tail |
| Citation-based lineage | paper cites the origin of the task | BrainMap "First:" citations; hed-task `historical` reference role; Experiment Factory `reference`. No dedicated paradigm-lineage citation-network study was found; co-citation work exists only at field level | a provenance facet; author/lab reuse |

---

## 8. Synthesis: recommended facets for a meta-analysis-oriented task schema

**Design principles from the review:**
1. Separate the **paradigm identity** (a canonical task plus a named variant) from the **compositional description** (per-condition stimulus / instruction / response). CogPO, BrainMap and hed-task all converge on this. Name-only systems (RDoC, NIH Toolbox, Psych-101) cannot answer "all visual, button-press, discriminate-instruction tasks".
2. Use **conditions and contrasts** as first-class objects, as Cognitive Atlas, NeuroVault and HED `Condition-variable` do. Meta-analysis selects contrasts, not tasks.
3. Make **constructs** a separate layer reached through contrasts (the CogAt `asserts` pattern), never a property of the task name alone.
4. Store **provenance**: an origin citation (BrainMap "First", hed-task `historical`) separate from usage citations, plus implementation and stimulus-set identifiers.
5. Keep relations **typed and directional**: `variant_of` (hed-task variations), `is_a` (CogPO/NIF subclassing), `part_of`/`in_battery` (CogAt), `combines` (Experiment Factory `X_with_Y` dual tasks). CogAt's edges show what happens when direction is not validated.

| Facet | Values / structure | Reusable vocabulary | Notes |
|---|---|---|---|
| `canonical_task` | ID + name + aliases + definition + inclusion test | **hed-task** (103 tasks, `inclusion_test{procedure, manipulations, measurements}`); **CogAt** tasks (857, IDs used by BIDS/NeuroVault/ExpFactory); **BrainMap Paradigm Class** (115, with definitions); CogPO (83) | crosswalk CogAt ↔ CogPO ↔ BrainMap ↔ hed-task (hed-task `data/mappings/*.tsv` already provides this) |
| `variant` | named variation of a canonical task + what differs | hed-task `variations` (776); BrainMap sibling classes (Stroop-Color/-Emotional/...) | express the delta through facet values (e.g., stimulus_kind=faces for "face n-back") |
| `task_family` | coarse grouping | hed-task 19 families; BrainMap 5 Behavioral Domains; CogAt 10 concept classes (= TaskExtractor `Domain`) | multi-valued, with primary/secondary roles (hed-task pattern) |
| `stimulus.modality` | Visual/Auditory/Tactile(+electrical/pain/pressure/thermal)/Olfactory/Gustatory/Interoceptive/Vestibular | CogPO Stimulus Modality; BrainMap (7); HED `Sensory-presentation` | per condition |
| `stimulus.kind` | Faces, Words, Pseudowords, Tones, Pictures, Scenes, Monetary amounts… | **BrainMap Stimulus Type (68)** ⊃ CogPO (41); hed-task stimulus_kind (46); HED `Item/Language-item` | BrainMap's list is the largest curated set |
| `stimulus.content` / manipulated dimension | Emotion(±), Congruence, Semantics, Reward, Color, Motion… | **BrainMap Stimulus Content (17)** | closest existing vocabulary for "manipulations" |
| `stimulus.role` | target, non-target, distractor, cue, feedback, reward, oddball, go/stop signal, prime, novel | **HED Task-stimulus-role (22)**; hed-task (12) | event/condition level |
| `stimulus.set` | named stimulus database (IAPS, NimStim, KDEF, Ekman, …) + version | none formal; hed-task descriptions mention IAPS/GAPED/NAPS/OASIS as free text | needs a new controlled list; high value for meta-analysis |
| `instruction` / judgment | Attend, Detect, Discriminate, Encode, Recall, Rate, Inhibit, Compare, Choose… | **BrainMap Instruction (46)** ⊃ CogPO (17); HED `Action/Think` (21); hed-task (32) | BIDS `Instructions` holds the verbatim text |
| `response.kind` | Button Press, Speech (overt/covert), Saccade, Rating, No response… | BrainMap Response Type (22); CogPO (overt 17 + covert); hed-task (23, adds key_press, mouse_click, touchscreen_tap, rating, no_response) | keep overt/covert explicit |
| `response.effector` | Hand, Foot, Ocular, Oral/Facial… | BrainMap Response Modality (10); CogPO FMA classes (8); HED `Move-body-part` | FMA IDs available through CogPO |
| `laterality` | Left/Right/Bilateral/Midline/Varying | BrainMap Stimulus/Response Laterality | optional |
| `design` | Blocked / EventRelated / Mixed; runs, trials, durations, timing | TaskExtractor `TaskDesign`; HED `Experimental-trial`, `Time-block` | design is not part of any paradigm ontology |
| `conditions` / `contrasts` | named conditions; contrasts as functions over conditions | CogAt Condition/Contrast model; HED `Condition-variable`; NeuroVault `contrast_definition` | link each contrast to constructs |
| `measures` / indicators | accuracy, RT, SSRT, d′, BOLD, ERP component, ratings | CogAt indicators (226 free-text values; normalize the top ~20); HED `Indicator-variable`; OntoNeuroLOG score/variable model | split behavioral vs neural measures |
| `constructs` | concepts measured, through a contrast | **CogAt concepts (918)** + `asserts`; hed-task processes (172); RDoC constructs (paradigm lists) | keep assertion provenance (who/which paper) |
| `context` | Normal Mapping, Disease, Pharmacology, Aging, Learning… | **BrainMap Context (12)** | study-level |
| `origin_citation` | DOI/PMID of the paradigm's source | BrainMap "First:"; hed-task `references.roles=historical`; ExpFactory `reference` | separate from usage citations (CogAt `has_citation` is untyped) |
| `implementation` | software/URI/version | CogAt Implementation; ExpFactory `exp_id`; PsychoPy/jsPsych | supports the lab-reuse signal |
| `battery` | WAIS-IV, NIH Toolbox, CANTAB, HCP tfMRI, SRO… | CogAt Battery (37) | `part_of` relation |
| `provenance.extraction` | source span, model, confidence | TaskExtractor fields; Turner 2025 practice | needed for LLM pipelines |

**Practical recommendations for this project:**
- **Normalization target:** use Cognitive Atlas task IDs, because they are already used by BIDS, NeuroVault and the Experiment Factory. Carry BrainMap Paradigm Class and hed-task IDs as crosswalks; hed-task already ships the CogAt and CogPO mappings.
- **Facets the LLM should extract** (beyond what TaskExtractor does now): stimulus modality/kind/content/set, instruction verb, response kind/effector, and origin citation. Restrict outputs to the BrainMap enumerations above. They are the largest curated lists, they contain the CogPO ones, and BrainMap coding provides the expert precedent (Turner 2013 baseline: stimulus modality is easy; paradigm class and stimulus type are hard from abstracts).
- **Task-vs-not-task gate:** BrainMap paradigm classes exclude analysis methods (DTI, VBM, connectivity). The TaskExtractor noise noted in JOURNAL.md ("diffusion tensor imaging", "vbm analysis") could be filtered by requiring a match to a paradigm class or an instruction/response facet.
- **Relatedness:** combine three signals:
  - facet-overlap distance (interpretable)
  - text-embedding distance of TaskDescription (CogText/Centaur style)
  - citation and author links (origin citation shared, lab reuse)
  Use Yeo 2015 components, the IBC/Varoquaux task→concept annotations, or Eisenberg factor loadings as external validation of any learned task space.

---

## Appendix A. BrainMap Paradigm Classes (115), verbatim from brainmap.org/taxonomy/paradigms/ (2026-10-09)

"First" is the origin citation given by BrainMap. "Most" is the second citation listed, apparently a representative or most-used exemplar; the page does not define it. "—" means none is listed.

| # | Paradigm Class | Definition (verbatim, BrainMap) | "First" citation | "Most" (exemplar) citation |
|---|---|---|---|---|
| 1 | Acupuncture | Stimulation with filamentous needles to elicit cognitive, behavioral, and/or physiological responses. | Han & Terenius, 1982 | Hui, et al. 2000 |
| 2 | Affective Pictures | Stimuli utilize affective images to elicit a range of emotions. | Cattell, Glascock & Washburn, 1918 | Cahill, et al. 2004 |
| 3 | Affective Words | Stimuli utilize words that are concerned with or arouse feelings or emotions. | Clore, Ortony & Foss, 1987 | Kensinger & Corkin, 2004 |
| 4 | Anti-Saccades | Make a saccade (directed rapid eye movement) away from target. | Hallett, 1978 | Paus, et al. 1993 |
| 5 | Braille Reading | Read Braille words with their finger(s). | Fertsch, 1946 | Sadato, et al. 1996 |
| 6 | Chewing/Swallowing | Chew edible or non-edible items, and may be asked to swallow the food/nonfood item. | Hollingworth, 1939 | Fraser, et al. 2002 |
| 7 | Classical Conditioning | Respond to a previously neutral stimulus that has been repeatedly paired with an unconditioned (positive/negative) stimulus that elicits the desired response. | Pavlov, 1927 | LaBar, et al. 1998 |
| 8 | Competition/Cooperation | Work together with another participant to achieve a common goal, or strive to gain/win something by defeating another participant. | Evans, 1965 | Rilling et al, 2002 |
| 9 | Controlled Breathing | a task in which the participant controls there own breathing or it is controlled mechanically; often used along with meditation, this task requires the subject manage the inhalation and exhalation of breath; can involve breathing through pursed lips, diaphragmatic breathing or deep breathing | — | — |
| 10 | Counting/Calculation | Count, add, subtract, multiply, or divide various stimuli (numbers, bars, dots, etc.) or solve numerical word problems. | Piaget, 1953 | Dehaene, et al. 1999 |
| 11 | Cued Explicit Recognition/Recall | A list of items (words, objects, textures, patterns, pictures, sounds) is presented and participants are subsequently tested with cues to recall previously presented material. | Tulving & Osler, 1968 | Henson, et al. 1999 |
| 12 | Deception | Perform a task and either lie or be truthful in his/her response. | Yerkes & Berry, 1909 | Langleben, et al. 2001 |
| 13 | Delay Discounting | Perform a reward task, and is asked to choose between a small immediate reward or large delayed reward. | Loewenstein, 1987 | McClure, et al. 2004 |
| 14 | Delayed Match to Sample | A stimulus that is followed by a probe item after a brief delay; subject is then asked to recall if the probe item was presented before the delay. | Sternberg, 1969 | Smith, Jonides & Koeppe, 1996 |
| 15 | Divided Auditory Attention | Respond to an auditory stimuli (tone or word) while performing an unrelated task. If the participants are presented with tones, then this is also often co-coded with Tone Monitor/Discrimination. | Cherry, 1953 | Anderson, et al. 2000 |
| 16 | Drawing | Draw lines, circles or more complex figures using a pen or stylus. | Greenspoon & Foreman, 1956 | van Mier, et al. 1998 |
| 17 | Driving | Control the operation and movement of a vehicle in a real or simulated driving environment. | Gibson & Crooks, 1938 | Hsieh, et al. 2008 |
| 18 | Drug Challenge | a task in which the sole point of the task is to look at the effects of a certain drug | — | — |
| 19 | Emotion Induction | Stimuli with emotional valence (e.g., statements, films, music, pictures) to induce effect on mood. | Velten, 1968 | Lieberman, et al. 2007 |
| 20 | Emotional Body Language Perception | The recognition of emotions expressed by another’s body pose, posture or body movement. Tasks usually require participants to infer the emotional meaning of non-verbal stimuli by paying particular attention to head, hand and body cues in the judgment of emotionally valent criteria. Based on popular beliefs that certain body postures communicate things like deceit/lying, pain/discomfort and sexual interest and cognitive neuroscience models that the purport that the visual system analyzes human motion differently from object motion. | Mattick, 1967 | Grèzes, Pinchon, & de Gelder, 2006 |
| 21 | Encoding | Memorize stimuli such as words, pictures, letters, etc. Includes Incidental Encoding, which is a task in which the participant is creating new memories without purposely knowing that memorization is the task at hand. Participants’ memories are created through working in their environment and picking up information in the process. | Tulving & Pearstone, 1966 | Henson, et al. 1999 |
| 22 | Episodic Recall | Recall from episodic memory (autobiographical, long-term memories) in a guided/unguided manner. Episodic information can be personal experiences as well as the specific objects, people, and events experienced at a particular time and place and can involve, for example, items defined as constituting discrete story elements or personal memories such as those elicited from each participant during a pre-scanning interview and then recalled via recording/script in the scanner. Recall of memories to elicit emotions such as happiness or sadness, should be co-coded with Emotion Induction. | Tulving, 1972 | Mayberg, et al. 1999 |
| 23 | Estimation | Calculate approximately the amount, extent, magnitude, position, or value of something. | Kaufman & Lord, 1949 | Herwig, et al. 2011 |
| 24 | Face Monitor/Discrimination | View face passively or discriminate human faces according to their order, gender, location, emotion, or appearance, etc. If the participants view the faces passively, then the experiment is co-coded with Passive Viewing. | Langfeld, 1918 | Whalen, et al. 1998 |
| 25 | Figurative Language | Respond to items/statements that convey non-literal/figurative language. Figurative language includes: similes, metaphors, personification, alliteration, onomatopoeia, hyperbole, idioms, proverbs, irony, sarcasm, metonymy, and cliché. | Myers, 1940 | Aziz-Zadeh, et al. 2006 |
| 26 | Film Viewing | View movies or film clips. | Emery, 1959 | Buccino, et al. 2001 |
| 27 | Finger Tapping/Button Press | Tap fingers or press a button in a cued/non-cued manner. Used for all experiments with a response type of Finger. | Shimoyama, Ninchoji & Uemura, 1990 | Colebatch, et al. 1991 |
| 28 | Fixation | Direct attention or gaze toward a visual stimulus, often a cross. | Hackman & Guilford, 1936 | Corbetta, et al. 1991 |
| 29 | Flanker | Respond to target stimulus that is surrounded by distracting or facilitating stimuli. | Eriksen & Spencer, 1969 | Ullsperger & Cramon, 2001 |
| 30 | Flashing Checkerboard | Flashing or reverse high contrast checkerboard. | Spehlmann, 1965 | Moradi, et al. 2003 |
| 31 | Flexion/Extension | Move (flex and extend) hands, arms, legs, feet, lips, tongue, etc. | Dearborn, Spindler & Delabarre, 1897 | Dapretto, et al. 2005 |
| 32 | Fluency Induction | Perform different fluency tasks in order to enhance the smoothness or flow with which sounds, syllables, words and phrases are joined together when speaking quickly. Tasks often including: verbal (semantic and/or phonological), perceptual (frequency, duration, font size, ease/difficulty to understand, and/or attractiveness), or speech production (masking, chorus reading, whispering, rhythmic stimulation, metronome pacing). | Fletcher, 1914 | Watkins, et al. 2007 |
| 33 | Free List Word Recall | Study a list of words presented in different order on successive trials; and then prompted to recall the items in any order. | Waugh, 1961 | Fize, et al. 1996 |
| 34 | Gambling | Make decisions about chance gambles. | Tversky & Kahneman, 1974 | Izuma, Saito & Sadato, 2008 |
| 35 | Go/No-Go | Perform a binary decision (go or no-go) on a continuous stream of stimuli. | Drewe, 1975 | Konishi, et al. 1999 |
| 36 | Grasping | Grasp or grip a presented stimulus with their hand or mimic grasping one that is not physically present (i.e., imaginary or presented as a picture or video). | Jeannerod, 1981 | Stephan, et al. 1995 |
| 37 | Hand-Eye Coordination | Coordinate eye movement with hand movement to process visual input and guide a behavioral response (i.e., spatial/orientation discrimination, motor planning, timing, monitoring, response selection, motor [sequence] learning). | Korins, 1934 | Farrer, et al. 2004 |
| 38 | Hunger/Satiety | The desire to eat, or to satisfy one's appetite. Measures often include pre-post hunger and satiety state, and/or hedonic value (reward/punishment) of food or solution. | Matsuda, et al. 1999 | Small, et al. 2001 |
| 39 | Hypercapnia/Air Hunger | The state of excessive carbon dioxide in the bloodstream, typically caused by inadequate respiration. Classically known as respiratory distress or air-hunger, it can be experimentally induced by having the subject perform a static apnea or breath-holding task; by training subjects to use a mechanical ventilator or using an experimenter-controlled air-supply device; or by having the subject inhale different mixtures of oxygen and carbon dioxide. | Opie, Smith & Spalding, 1959 | Evans, et al. 2002 |
| 40 | Imagined Movement | Subjects imagine performing some motor task (e.g., walking, reaching). | Jacobson, 1932 | Grafton, et al. 1996 |
| 41 | Imagined Objects/Scenes | Visualize patterns, objects, scenes, places, concepts, real/hypothetical events (not from personal memories), in a cued/non-cued manner. | Overton & Jackson, 1973 | Ochsner, et al. 2002 |
| 42 | Induced Panic | Experimentally induced panic created by injection or inhalation of chemicals, usually done to create trigger symptoms in individuals that resemble those of panic attacks or anticipatory anxiety. | Reiman, et al. 1986 | Eser, et al. 2009 |
| 43 | Isometric Force | Use hands or fingers to apply isometric force or complete a precision grip task. | Hartree & Hill, 1921 | Ehrsson, Fagergren & Forssberg, 2001 |
| 44 | Lexical Decision | Discriminate between words and pseudowords (orthographically and phonologically legal nonwords). | Meyer & Schvaneveldt, 1971 | Farrer, et al. 2004 |
| 45 | Lip Pursing/Tongue Movement | a task which requires the participant to purse their lips or protrude their tongue or move their tongue side-to-side or up and down | — | — |
| 46 | Lower-body Negative Pressure (LBNP) | Lower-body Negative Pressure (LBNP)- is a task in which the blood from the upper body is redistributed to the pelvis and legs, thus reducing central venous pressure and venous return; the subject is placed in an air-tight metal tank, which is then sealed, and sub-atmospheric pressure is produced using a vacuum pump | — | — |
| 47 | Magnitude Comparison (Distance) | Perform a task in which the distance between stimuli is estimated. | Gilinsky, 1951 | Bartolo, et al, 2014 |
| 48 | Magnitude Comparison (Luminance) | Perform a task in which the luminance or intensity of light between stimuli is estimated. | Herrick 1956 | Pinel et al, 2014 |
| 49 | Magnitude Comparison (Non-symbolic/Numerical) | Perform a task in which the differences between non-symbols or numbers is estimated (e.g., choose the more numerous array of dots). | Buckley & Gillman, 1974 | Venkatraman et al, 2006 |
| 50 | Magnitude Comparison (Physical Size) | Perform a task in which the physical size between stimuli is estimated. | Singer, 1952 | Lewis & Miall, 2003 |
| 51 | Magnitude Comparison (Symbolic/Numerical) | Perform a task in which the differences between symbols or numbers is estimated (e.g., choose the larger Arabic numeral or number). | Moyer & Landaur, 1967 | Pesenti et al, 2000 |
| 52 | Meditation | Conscious mental process that induces a relaxation response. Concominant measures often include cognitive, behavior, and or physiological activity. | Anand, Chhina & Singh, 1961 | Lazar, et al. 2000 |
| 53 | Mental Rotation | Mentally rotate visually presented 2D and 3D figures. | Shepard & Metzler, 1971 | Kosslyn, et al. 2003 |
| 54 | Micturition | Think about voiding urine, or provide urine samples. | Tang & Ruck, 1956 | Blok, Willemsen & Holstege, 1997 |
| 55 | Motor Learning | Repeatedly execute a motor task to improve performance. | Sanderson, 1929 | Anguera, et al. 2007 |
| 56 | Multi-Tasking | Perform simultaneous execution of one or more tasks that can be presented in different modalities. | Shallice & Burgess, 1991 | Bowyer, 2009 |
| 57 | Music Comprehension | Listen to tones, melodies, chords, dissonant/consonant music, rhythms, spoken lyrics, musical excerpts/notes. | Brust, 1980 | Halpern & Zatorre, 1999 |
| 58 | Music Production | Produce music by singing (overly/covertly), or by playing an instrument. | Sergent, et al. 1992 | Halpern & Zatorre, 1999 |
| 59 | Naming (Covert) | View objects (pictures, line drawings, etc.) and name them silently. | Martin, et al. 1996 | Same as First |
| 60 | Naming (Overt) | View objects (pictures, line drawings, etc.) and name them aloud. | Ligon, 1932 | Martin, et al. 1996 |
| 61 | Object Manipulation/Discrimination | Physically interact with one or more objects, and/or discriminate between its physical (shape, color, texture) and/or semantic properties (use, previous experience, relationship to other objects). | Tatarsky, 1974 | Stephan, et al. 1995 |
| 62 | Oddball Discrimination | Detect the presence of an oddball (infrequent/distinct) stimulus from a continuous stream of stimuli. Examples include when participants listen to tones and indicate when they hear a target tone (oddball) or when participants view letters or objects and indicate when they see a target stimulus (oddball). | Sutton, et al. 1965 | Braver, et al. 2001 |
| 63 | Olfactory Monitor/Discrimination | Smell odors passively and/or discriminate according to some feature (pleasant/unpleasant, strong/weak, same/different, etc.). | Adrian, 1950 | Wicker, et al. 2003 |
| 64 | Orthographic Discrimination | View letters and discriminate according to some written/printed feature (i.e., upper–case/lower–case, alphabetic order, same/different spelling of words, vowel/consonant, font type/size). | Reicher, 1969 | Oldrack, et al. 1999 |
| 65 | Pain Monitor/Discrimination | Stimulation (i.e., thermal, electrical, tactile) at a painful threshold. | Hardy, Wolff & Goodell, 1947 | Singer, et al. 2004 |
| 66 | Paired Associate Recall | Encode paired items, and subsequently asked to recall the associated pair. | Feldman & Underwood, 1957 | Paus, et al. 1993 |
| 67 | Passive Listening | Listen to auditory stimuli (speech, noise, tones, etc.) and make no response. If the participants are presented with tones, then this is also often co-coded with Tone Monitor/Discrimination. If the participants are presented with music, i.e., a melody not just tones, then code as Music Comprehension. | Nichols, 1948 | Mayberg, et al. 1999 |
| 68 | Passive Viewing | View visual stimuli (objects, faces, letter strings, etc.) and make no response. If the presented stimuli are faces, the experiments are co-coded with Face Monitor/Discrimination. If presented stimuli are words, the experiments are not coded as passive viewing but rather as Reading (Covert). | Alexander & Barrett, 1975 | Corbetta, et al. 1993 |
| 69 | Phonological Discrimination | View or listen to phonemes, syllables, or words and discriminate according to some feature of their sounds (rhyming, number of syllables, homophones, pronounceable nonwords, etc.). | Liberman, et al. 1957 | Demonet, et al. 1992 |
| 70 | Pitch Monitor/Discrimination | Listen passively or discriminate stimuli (human speech and non-speech vocalizations, animal vocalization, mechanical noise, etc.) based on pitch (i.e., duration, familiarity, pleasantness, gender, frequency). If participants only listen passively, then also co-code with Passive Listening. | Knudsen, 1923 | Royet, et al. 2000 |
| 71 | Pointing | Point at a target mentally or physically (e.g., point with finger, or imagine pointing with finger). | Peterson, 1965 | Simon, et al. 2002 |
| 72 | Pursuit Rotor/Manual Tracking | Follow/pursue a small disc on a rotating turntable. Co-coded with Motor Learning, if participants are given practice trials to improve performance and accuracy. | Ammons, 1955 | Grafton, et al. 1992 |
| 73 | Reading (Covert) | Silently read words, pseudo-words, characters, phrases, or sentences. | Locke, 1971 | Petersen, et al., 1988 |
| 74 | Reading (Overt) | Read aloud words, pseudo-words, logograms, phrases, or sentences | Haber & Haber, 1982 | Turkeltaub, 2002 |
| 75 | Reasoning/Problem Solving | Make judgements, inferences, generalizations and/or conclusions through the use of logic. Tasks can include integration of different elements/information, probabilistic classification, text comprehension, falsification of a conditional rule, and word problems. | Golding, 1981 | Aziz-Zadeh, et al. 2006 |
| 76 | Recitation/Repetition (Covert) | Silently repeat or recite phonemes, words, or well-known text (nursery rhymes, Pledge of Allegiance, months of the year, etc.). | Gagné & Smith, 1962 | Warburton, et al. 1996 |
| 77 | Recitation/Repetition (Overt) | Repeat or recite aloud phonemes, words, or well-known text (nursery rhymes, Pledge of Allegiance, months of the year, etc.). | Gagné & Smith, 1962 | Petersen, et al., 1988 |
| 78 | Reward | A stimulus that serves the role of reinforcing a desired response. Participants perform a task in which correct performance is associated with reward, often monetary reward. | Lorge, 1933 | O'Doherty, et al. 2001 |
| 79 | Saccades | Perform a rapid eye movement or saccade to capture an object in the visual field. | Stark, Vossius & Young, 1962 | Corbetta, et al. 1998 |
| 80 | Self-Reflection | Meditate or think about one's character, actions, and motives. Co-code with the paradigm Meditation if this is part of a meditation task. | Pollack, et al. 1962 | Modinos, Ormel & Aleman |
| 81 | Semantic Monitor/Discrimination | Discriminate between the meanings of individual lexical items or to indicate if target word is semantically related to the probe word. Stimuli in discrimination tasks can be words or pictures representing words. | Xiang, et al. 2003 | Demonet, et al. 1992 |
| 82 | Sequence Recall/Learning | Learn and/or perform a complex sequence of finger tapping, button pressing, pointing/clicking, or various other motor responses. | Wilding & Mohindra, 1980 | Jenkins, et al. 1994 |
| 83 | Sexual Arousal/Gratification | Induction of sexual readiness with or without sexual climax. | Zuckerman, 1971 | Seftel, 2010 |
| 84 | Sleep | Sleep with or without sleep stage monitoring. | Johnson, Swan & Weigand, 1926 | Lerner, et al. 2007 |
| 85 | Stroop-Color | Name the color of the ink for a list of words (color names) printed in congruent/incongruent colors, or determine if ink color and color name are congruent/incongruent. Color-congruent stimuli: ink color and color name are the same (e.g., the word GREEN printed in green ink). Color-incongruent stimuli: ink color and color name differ (e.g., the word GREEN printed in red ink). | Stroop, 1935 | MacDonald, et al. 2000 |
| 86 | Stroop-Counting | Report the number of words presented regardless of the word meaning. Congruent stimuli: semantic meaning and numerical value match (e.g., word TWO presented twice on the screen). Incongruent stimuli: semantic meaning and numerical value differ (e.g., word TWO presented four times). Neutral stimuli: semantic meaning and numerical value are unrelated (e.g., word DOG presented four times). | Reisberg, Baron & Kemier, 1980 | Bush, et al. 1999 |
| 87 | Stroop-Emotional | Name the ink color of emotionally charged words (i.e., positively or negatively valenced words). | Whalen, et al. 1998 | Watts, et al. 2011 |
| 88 | Stroop-Other | Allocate attentional resources to process a specific stimulus feature in a context with competing (interfering), typically more prepotent, information. | Shor, 1975 | Huang, et al. 2011 |
| 89 | Stroop-Spatial | The spatial Stroop effect demonstrates interference between the stimulus location with the location information in the stimuli. It is elicited when the direction of the arrow is incompatible with its spatial location. For example, subjects are presented with a word either to the right or left of a central fixation point. For congruent trials, subjects see either the word ‘right’ presented to the right of fixation, or the word ‘left’ presented to the left of fixation. For incongruent trials, subjects see either the word ‘right’ presented to the left of fixation or the word ‘left’ presented to the right of fixation. | Shor, 1998 | Schmitz, et al. 2005 |
| 90 | Syntactic Discrimination | Discriminate between grammatically correct and incorrect sentences. This class also includes morphosyntactic tasks such as gender discrimination of words. | Dennis & Kohn, 1985 | Wartenburger, et al. 2003 |
| 91 | Tactile Monitor/Discrimination | Manipulate, recognize and/or discriminate objects through touch (i.e., shape, texture, same-different). | Lamb, 1983 | Paus, et al. 1993 |
| 92 | Task Switching | Switch from one task or goal to another. | Spector & Biederman, 1976 | Braver, Reynolds & Donaldson, 2003 |
| 93 | Taste | Discriminate/rate flavor intensity, pleasantness, solution content (i.e., fat content) of an item, food, or solution with or without swallowing the item. Participants may be asked to evaluate the affective significance of other stimuli (i.e., pictures, words, objects) when paired with food. | Gowers, 1882 | Hare, Camerer & Rangel, 2009 |
| 94 | Theory of Mind | Understand another's personal beliefs and feelings or form hypotheses regarding the mental states of others. | Gallagher & Frith, 2003 | Ochsner, et al. 2004 |
| 95 | Thirst Induction | Inducing a sensation of dryness in the mouth and throat associated with a desire for liquids; dehydration. | Giddan, 1966 | Egan, et al. 2003 |
| 96 | Tone Monitor/Discrimination | Listen to tones passively or discriminate according to a sound property (e.g., order, timing, pitch, frequency, amplitude), and/or detect presence/absence of a tone. | Strainer, et al. 1997 | Critchley, et al. 2004 |
| 97 | Tower of London | Mentally or physically rearrange a set of three (or more) colored beads/discs arranged on pegs, in the fewest possible moves, to match a specified configuration. Also includes Tower of Hanoi tests for taxonomic parsimony. | Shallice, 1982 | van den Heuvel, et al. 2005 |
| 98 | Transcranial Magnetic Stimulation | Electromagnetic pulses are applied at the scalp to induce electrical currents in the brain (TMS). | Barker, Jalinous & Freeston, 1985 | Fox, et al. 1997 |
| 99 | Trauma Recall | Cued recall/re-experience of a previous traumatic event. Often achieved using a patient-generated script or set of cues calling to mind the trauma. | Burgess & Holmstrom, 1979 | Bremner, et al. 2003 |
| 100 | Urine Witholding | a task that usually requires that the subject withhold urine with a partially full or full bladder, while controlling voiding | — | — |
| 101 | Vestibular Stimulation | Vestibular (labyrinthine) excitability under caloric, mechanic, or turning stimulation. Galvanic Vestibular Stimulation: uses direct current electricity stimulation to stimulate vestibular system. Also includes Caloric Vestibular Stimulation, a task in which cold and warm water to stimulate the vestibular system. | Atkinson, 1939 | Bottini, et al. 1994 |
| 102 | Vibrotactile Monitor/Discrimination | Vibrotactile stimulation (perception of vibration through touch) to skin or joints. | Verrillo, 1963 | Coghill, et al. 1994 |
| 103 | Video Games | Play video games often to measure emotional changes (e.g., aggression), perceptual learning/transfer of skills, or skilled vs. unskilled players. | Jones, Kennedy & Bittner, 1981 | Mathaik & Weber, 2006 |
| 104 | Visual Motion | Infer the speed and direction of elements in a scene based on visual input, or discriminate between coherent/incoherent biological motion. | Ludvigh, 1949 | Deutschländer, et al. 2002 |
| 105 | Visual Object Identification | Identify an object based on its visual attributes (e.g., shape, color, viewing angle), or detect/discriminate changes on the object's visual properties (e.g., size, illumination, position, relation between parts). | Beauvois, 1982 | Lu, et al. 2009 |
| 106 | Visual Pursuit/Tracking | Observe a moving target(s) and track its movement across the screen, or track visual changes on the moving target (e.g., velocity, trajectory, location in space). | Barten, Birns & Ronch, 1971 | Corbetta, et al. 1991 |
| 107 | Visuospatial Attention | Make cued/noncued shifts of visual attention to a particular spatial location in the visual field. Responses can be overt (with eye movement to target location) or covert (fixating on a central target while paying attention to spatial location changes of peripheral target). Also includes the Posner and Simon task. | Eriksen & Hoffman, 1972 | Paus, et al. 1993 |
| 108 | Wisconsin Card Sorting Test | Sort cards into groups based on some dimension (i.e., color, form, or number) that is changed intermittently, and requires participants to identify a new correct group dimension. | Berg, 1947 | Monchi, et al. 2001 |
| 109 | Word Generation (Covert) | Semantic: Listen to or view nouns and silently generate an associated verb, or view a category and silently generate as many exemplars as possible. Orthographic: Listen to or view a letter and silently generate as many words as possible that start with that letter. Phonologic: Listen to or view a word and silently generate words that rhyme. | Friston, et al. 1995 | Same as First |
| 110 | Word Generation (Overt) | Semantic: Listen to or view nouns and overtly generate an associated verb, or view a category and overtly generate as many exemplars as possible. Orthographic: Listen to or view a letter and overtly generate as many words as possible that start with that letter. Phonologic: Listen to or view a word and overtly generate words that rhyme. | Petersen, et al., 1988 | Same as First |
| 111 | Word Imageability | Participants are presented with a task that reflects how easy or difficult it is to imagine a word. | Paivio, Yuille & Madigan, 1968 | Sabsevitz, et al. 2005 |
| 112 | Word Stem Completion (Covert) | Silently generate a word that completes the word stem. | Graf, Mandler & Haden, 1982 | Buckner, et al. 2000 |
| 113 | Word Stem Completion (Overt) | Overtly generate a word that completes the word stem. | Warrington & Weiskrantz, 1970 | Heckers, et al. 1998 |
| 114 | Writing | Write letters or words with a pen, stylus, or their finger. | Pennebaker, 1997 | Longcamp, et al. 2003 |
| 115 | n-back | The state or process of overtly moving. *(sic: this is the text on the BrainMap page, apparently pasted from Action.Execution by mistake)* | — | — |
