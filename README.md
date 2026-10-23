# Paradigm Atlas

Code and derived data behind the **Paradigm Atlas**, a browser of the 224 canonical experimental tasks found in
about 33,000 neuroimaging papers (39,096 task mentions). For each task it shows how papers name it, the conditions
it uses, the qualifiers that vary between versions, the papers it descends from, the labs that run it, and related
tasks. The built page is [`site/paradigm_atlas.html`](site/paradigm_atlas.html), a single self-contained file.

A task's identity follows the [hed-task](https://github.com/hed-standard/hed-task) rule: a task is defined by its
procedure. Names, stimuli and populations are recorded as qualifiers. Results and design decisions are in
[`docs/REPORT.md`](docs/REPORT.md).

## Workflow

The workflow has three stages. Stages 1 and 2 ran on a GPU server holding the
[ns-pond](https://github.com/neurostuff) full-text corpus (61,283 papers); stage 3 runs locally on CPU.

### 1. Corpus inputs (server)
1. **Manifest.** `scripts/build_manifest.py` lists ids and available text sources for each paper.
2. **Task mentions.** `scripts/collect_taskextractor.py` flattens TaskExtractor 1.1.0 outputs into one row per
   mention: name, description, conditions → `data/taskextractor/te_tasks.jsonl`.
3. **PubMed metadata.** `scripts/fetch_pubmed_meta.py` fetches year and authors; the last author stands in for the lab.
4. **Citations near mentions.** `scripts/build_bibliographies.py` parses JATS/Elsevier reference lists, and
   `scripts/harvest_te_citations.py` resolves the citation markers next to each task name →
   `te_citations.jsonl` and `te_citations_ctx.jsonl` (the second also keeps the citing sentence).
5. **Procedure embeddings.** `scripts/embed_te_procedures.py` embeds each description with Qwen3-Embedding-0.6B,
   with task names masked out.

### 2. TaskCard facet profiles (server, GPU)
These produce the per-task "typical profile" (stimuli, modality, response, design).
1. **Passages.** `scripts/build_passages.py` and `build_passages_psych.py` select the Methods passages that describe
   tasks.
2. **Silver labels.** `scripts/silver_label.py` labels 1,200 neuroimaging papers and 169 psychology papers with
   an LLM, using the TaskMention template in `taskcat/template.py`.
3. **Fine-tune.** NuExtract3 is fine-tuned with QLoRA on the silver labels (`scripts/build_train_data_v2.py`,
   `ft/start_task_v{1,2,3}.sh`) and served with vLLM (`ft/after_train_v*.sh`). `ft/merge_task.py` imports
   `ckpt_io`, a server-side helper that is not included here.
4. **Extract and assemble.** `scripts/nuextract_infer_2pass.py` runs the extractor (`scripts/scaleup_v2.sh`,
   `after_v3_chain.sh`), and `scripts/build_taskcards.py` normalizes the extractions into TaskCards (`taskcat/cards.py`).

### 3. Normalization and atlas build (local)
| step | script | output |
|---|---|---|
| Give each mention a canonical task. A gate first drops non-tasks; four routes then propose a label: **A** matches the name against the lexicon (hed-task plus `tct_*` extensions), **B** is a classifier on the masked procedure embedding, **C** votes from shared citations, **D** uses the senior author's other papers. `taskcat/normalize.py::combine` merges the routes. | `normalize_te.py` | `te_normalized.jsonl` |
| Normalize condition names into axis:value atoms and phases, then derive one condition schema per task | `condition_schemas.py` | `condition_schemas.json` ✓ |
| Rank the references cited near each task by papers × purity to find origin papers (hypothesis H8) | `h8_origin_discovery.py` | `discovered_origins.json` ✓ |
| Compute task–task similarity from procedure, co-citation and senior-author signals (hypothesis H9) | `h9_task_relatedness.py` | `task_sim_combined.npy`, `task_sim_tasks.json` ✓ |
| Aggregate per-task summaries and add the TaskCard profiles from stage 2 | `build_explorer_data.py` | `data/explorer.json` ✓ |
| Inject the data into `scripts/explorer_template.html` | `render_explorer.py` | `site/paradigm_atlas.html` ✓ |

Run every script from the repository root. Outputs marked ✓ are committed. `data/explorer_hyps.json` holds the
"What the corpus showed" table; it was written by hand from the hypothesis tests (`scripts/h*.py`) and has no
generating script.

### Rebuild the page from the committed data
```bash
python scripts/render_explorer.py    # standard library only
# earlier steps: pip install rapidfuzz numpy scikit-learn pandas sentence-transformers requests pyyaml lxml
```
This reproduces `site/paradigm_atlas.html` byte for byte. Rerunning earlier steps needs the upstream files listed
below.

## Data

**Committed** (derived aggregates, about 2 MB):
- `data/explorer.json`, `data/explorer_hyps.json`: the page data
- `data/taskextractor/{condition_schemas,discovered_origins}.json`, `task_sim_combined.npy`, `task_sim_tasks.json`
- `data/external/hed-task/`: the hed-task catalog at commit 1815e8c (MIT, see its LICENSE), which feeds the lexicon
- `data/external/brainmap_crosswalk.json`: BrainMap paradigm classes ↔ inventory
- `schema/task_inventory_v3.json` (task ontology), `schema/task_relations.json`, `schema/task_schema.yaml`,
  `schema/study_schema_crosswalk.md`

**Not committed.** These files are large or contain sentences quoted from copyrighted full text:

| file | size | made by |
|---|---|---|
| `data/manifest.jsonl` | 31 MB | `build_manifest.py` |
| `data/taskextractor/te_tasks.jsonl` | 57 MB | `collect_taskextractor.py` (contains paper text) |
| `data/taskextractor/te_proc_emb.npy`, `te_proc_meta.jsonl` | 99 MB | `embed_te_procedures.py` |
| `data/taskextractor/te_citations.jsonl`, `te_citations_ctx.jsonl` | 109 MB | `harvest_te_citations.py` (ctx contains paper text) |
| `data/taskextractor/te_normalized.jsonl` | 15 MB | `normalize_te.py` |
| `data/pubmed/meta_*.jsonl` | 240 MB | `fetch_pubmed_meta.py` |
| `data/cards/{gold_v2,train_luna_v2,train_rest_v2,psych_v3}.jsonl` | 80 MB | `build_taskcards.py` (contains evidence spans) |
| `data/passages_*.jsonl`, `data/silver/`, model checkpoints | — | stage 2 |

## Layout
- `taskcat/`: the library (sectioning, templates, validation, citations, bibliographies, PubMed client, lexicon,
  normalizer, decomposition, facets, conditions, TaskCards, study_schema emitter)
- `scripts/`: pipeline steps and hypothesis tests (`h1`…`h12`); `ft/`: fine-tuning and serving scripts
- `schema/`: the task ontology and schemas; `docs/`: the report and background summaries
- Credentials are read from environment variables only: `PUBMED_API_KEY` and `EMAIL` (`taskcat/pubmed.py`),
  `OPENAI_API_GATEWAY` and `OPENAI_API_KEY` (`taskcat/llm.py`). The default `.env` paths in those modules point
  at the original server.
