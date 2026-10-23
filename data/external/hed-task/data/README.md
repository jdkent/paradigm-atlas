# The Catalog's data

Everything the site is generated from lives here and is edited here, by pull request.

| File                    | What it holds                                                                                                                                                                       | Edited how                                                                                     |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `task_details.json`     | The tasks: identifiers, names and aliases, definitions, inclusion tests, variations, process links, references                                                                      | By hand, in a PR; validated by the schema and by `src/generate_docs.py`                        |
| `process_details.json`  | The processes and their categories: definitions, aliases, references, linked tasks                                                                                                  | Same                                                                                           |
| `schemas/*.schema.json` | JSON Schemas (draft-07) for the two files above; editors that understand them flag shape errors as you type                                                                         | Rarely; when the record shape changes                                                          |
| `mappings/*.tsv`        | The curated correspondence with the Cognitive Atlas, one row per entity; see `mappings/README.md`                                                                                   | By hand; `src/build_atlas_maps.py` refreshes the descriptive columns without touching curation |
| `atlas_summary.json`    | Statistics about the Cognitive Atlas snapshot, for the Atlas essays                                                                                                                 | Recomputed by `src/build_atlas_data.py` from the archive                                       |
| `cogpo_summary.json`    | CogPO (Cognitive Paradigm Ontology) classes by branch, the paradigm list and the six dimension vocabularies                                                                         | Recomputed by `src/build_cogpo_data.py` from the archive                                       |
| `facet_defs.tsv`        | The facet vocabularies: stimulus modality, kind and role, response modality and kind, instructions, each value with its source (CogPO, HED, Catalog), definition and HED 8.4.0 tags | By hand; not yet used on task records                                                          |
| `task_family_defs.tsv`  | The task families: display order, name, scope                                                                                                                                       | By hand                                                                                        |

The two JSON files began as an export from the research workspace that found the citations (see `src/import_catalog.py`, kept as the record of that one-time migration). Since 2026-09-19 this directory is their home.

## Editing a task or process

1. Edit the JSON. Keep the file ASCII except inside recorded data (author names, titles), keep two-space indentation, and keep records in their existing order. The `inclusion_test` is three lists: `procedure` (ordered steps, each a sentence ending in a period), `manipulations` and `measurements` (one variable or measure per item, no final period; an item begins with a capital unless its first word is an initialism such as fMRI or a conventionally lowercase term such as d-prime). Every list has at least one item.
2. Run `python src/generate_docs.py`. It validates before writing: schema shape, unique identifiers, every `hed_process_ids` entry resolving to a process, every process's `tasks` list agreeing with the tasks that name it, `task_count` and the header counts, reference `roles` from the allowed vocabulary, and every variation carrying its derived `variation_id`. A failure names the record and writes nothing.
3. Commit the data and the regenerated pages together. CI regenerates and fails the PR if they disagree.

### Pseudo tasks

A record with `"task_kind": "pseudo_task"` is a block that serves the experiment around it rather than eliciting a process through trials: a baseline or reset (rest), a physical set-up (fixation), a self-report (questionnaire) or feedback on performance (task criteria, section "Pseudo tasks"). It may have an empty `hed_process_ids`, which means no links have been recorded, not that no process is engaged, and it must be filed under the `pseudo_tasks` family; the validator checks both. Ordinary tasks omit `task_kind`.

### Linking a task to a process

Add the process id to the task's `hed_process_ids`, and add the task to the process's `tasks` list (`{"hedtsk_id": ..., "canonical_name": ...}`) and bump its `task_count`. The validator checks that both sides agree.

### Adding a variation

Add `{name, description, justification}` to the task's `variations`, then run `python src/add_variation_ids.py` to assign the `variation_id` (or write it by hand as `hedvar_<task slug>__<variation slug>`; the validator will tell you the expected value).

### Adding a reference

A reference carries bibliographic fields, an `ids` block (`doi`, `pmid`, `openalex_id`, `pmcid`, `s2_id`, `arxiv_id`, any may be null), `oa_status`, a `citation_string`, and `roles`. Give every new reference a real role:

- `historical` for a paradigm-defining or foundational paper; it is published under "Key references" (tasks) or "Fundamental references" (processes)
- `review` for a review or meta-analysis, `experiment` for an empirical paper, `dataset` for a dataset paper, `other` when none fits

`unknown` is the legacy value on references imported before roles were curated; do not use it for new entries.

After adding or changing a reference, run `python src/check_references.py`. It compares each reference's citation string with the bibliographic record its DOI resolves to and reports the ones that disagree, which is how a DOI attached to the wrong paper is caught. A tool-filled DOI is not trusted until the two agree.

## Task families and process categories

A family groups tasks by what the participant does, not by which cognitive process the task is thought to measure. That is the same principle the task criteria use to decide whether two experiments are the same task: procedure first. The Catalog's process list covers the other axis, so the two views cross-link rather than duplicate one another. Categories group processes by research tradition in the same organizational spirit.

Families and categories are organizational, not a hierarchy (GitHub issue 28). A task or process may belong to several, so membership is a list on the record itself: `families` on a task in `task_details.json`, `categories` on a process in `process_details.json`. Each entry has:

- `family_id` or `category_id` - must exist in `task_family_defs.tsv` or in the `categories` array
- `role` - `primary` for the one family or category the record is filed under (its page holds the full entry; the sidebar and listings place it there), `secondary` for a cross-listing. Exactly one entry is `primary`.
- `confidence` - `high` (the default when omitted) or `review`. A `review` mark flags a judgement call for a second opinion: on the primary, "not sure this is the right home"; on a secondary, "not sure this belongs here at all". Review entries are listed under "Marked for review" on the family or category page.
- `rationale` - one line saying why; required on a secondary and on any `review` entry, naming the alternative or the doubt

A pseudo task belongs to the `pseudo_tasks` family only. The site documents the same rules in the [task family assignment](https://www.hedtags.org/hed-task/methods/task_criteria/06_task_family_assignment.html) and [process category rules](https://www.hedtags.org/hed-task/methods/process_criteria/04_process_category_rules.html) pages.

`task_family_defs.tsv`

- `family_id` - snake_case identifier, used in page paths and anchors
- `order` - display order on the task index and in the sidebar
- `name` - display name, sentence case
- `scope` - one or two sentences saying what procedure the family covers and what is measured

`src/generate_docs.py` fails if a record has no primary or more than one, lists a family or category twice, names an unknown id, omits a required rationale, or if a family or category has no primary member. A category's `process_count` must equal the number of processes filed under it.

The one-time move from the former `task_families.tsv` to the `families` field is recorded in `src/migrate_memberships.py`.
