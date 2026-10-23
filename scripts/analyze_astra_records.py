"""Task-centred statistics over the pondie pubget-astra-medium-100 extraction records.

    python scripts/analyze_astra_records.py [RUN_DIR] [--json out.json] [--top 50]

RUN_DIR defaults to the pubget_astra_medium_100 run inside the results bundle. Reads
records/*.extraction.json, corpus/<id>/processed/pubget/{text.txt,metadata.json} and
final-validation.json. Prints a plain-text report; --json also writes the raw numbers.
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import re
import statistics

DEFAULT = ("/home/jdkent/projects/StudyIESchema/pondie/"
           "pubget-astra-medium-100-results-20261008/runs/pubget_astra_medium_100")
TASK_FIELDS = ["name", "description", "design_type", "presentation_software", "instructions",
               "references", "stimuli", "stimulus_modality", "response_modality",
               "performance_measures"]
COND_FIELDS = ["name", "condition_kind", "description", "stimulus_content"]
NUMERIC_CITE = re.compile(r"^\[?\s*\d")


def spans_of(field):
    """All evidence spans of one ExtractedValue wrapper."""
    ev = (field or {}).get("evidence") or {}
    return [s for st in ev.get("sets") or [] for s in st.get("spans") or []]


def filled(field):
    return bool(field) and field.get("extraction_status") == "extracted" \
        and field.get("value") not in (None, "", [])


def values(field):
    v = (field or {}).get("value")
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def squash(s):
    return re.sub(r"\s+", "", s).lower()


def section_at(sections, pos):
    """Title of the deepest paper section containing character `pos`."""
    best = None
    for s in sections:
        if s["start_char"] <= pos < s["end_char"]:
            if best is None or s["level"] >= best["level"]:
                best = s
    return best["title"] if best else None


def top_section(sections, pos):
    """(deepest, top-level ancestor) section titles containing `pos`."""
    deepest = section_at(sections, pos)
    by_title = {s["title"]: s for s in sections}
    node = by_title.get(deepest)
    while node and node.get("parent_section") in by_title:
        node = by_title[node["parent_section"]]
    return deepest, (node or {}).get("title")


def section_class(sections, pos):
    """Coarse class from the top-level ancestor, falling back to the deepest heading."""
    deepest, top = top_section(sections, pos)
    c = coarse_section(top)
    return c if c != "other" else coarse_section(deepest)


def norm_name(name):
    """Loose grouping key: case, hyphens and trailing generic words removed."""
    n = re.sub(r"[-_\u2010-\u2015]", " ", name.lower())
    n = re.sub(r"\(.*?\)", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    n = re.sub(r"\b(functional mri|fmri|scan|protocol)$", "", n).strip()
    return n


def coarse_section(title):
    t = (title or "").lower()
    for key, words in [("methods", ["method", "material", "procedure", "paradigm", "task",
                                    "stimul", "design", "participant", "subject", "acquisition",
                                    "analysis", "fmri", "mri", "imaging", "experiment"]),
                       ("results", ["result"]), ("discussion", ["discussion", "conclusion"]),
                       ("introduction", ["introduction", "background"]),
                       ("abstract", ["abstract", "summary", "highlights", "key points"])]:
        if any(w in t for w in words):
            return key
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", default=DEFAULT)
    ap.add_argument("--json")
    ap.add_argument("--top", type=int, default=50)
    args = ap.parse_args()
    R = args.run_dir

    files = sorted(glob.glob(os.path.join(R, "records", "*.extraction.json")))
    out = {"n_records": len(files)}
    n_tasks_per = []
    no_task_ids = []
    name_counter = collections.Counter()
    norm_counter = collections.Counter()
    assess_type = collections.Counter()
    behav_assess = []
    name_papers = collections.defaultdict(set)
    field_fill = {f: collections.Counter() for f in TASK_FIELDS}
    cond_fill = {f: collections.Counter() for f in COND_FIELDS}
    enum_vals = {f: collections.Counter() for f in
                 ["design_type", "stimulus_modality", "response_modality"]}
    cond_kind = collections.Counter()
    ref_style = collections.Counter()
    ref_examples = []
    n_conditions = []
    span_total = span_exact = 0
    span_lens = []
    span_sections = collections.Counter()
    span_sets_per_field = collections.Counter()
    name_in_span = collections.Counter()
    verbatim = collections.defaultdict(collections.Counter)
    analyses_total = analyses_with_task = analyses_with_cond_cell = 0
    tasks_linked = tasks_total = 0
    hash_ok = 0
    meta_authors = 0
    ids_present = collections.Counter()
    models = collections.Counter()
    versions = collections.Counter()
    repaired = 0
    text_lens = []

    for f in files:
        sid = os.path.basename(f).split(".")[0]
        rec = json.load(open(f))
        meta = rec.get("extraction_metadata", {})
        models[meta.get("extractor_model")] += 1
        versions[meta.get("extractor_version")] += 1
        repaired += bool(meta.get("repaired_by"))
        sections = meta.get("paper_sections") or []
        cdir = os.path.join(R, "corpus", sid)
        text_path = os.path.join(cdir, "processed", "pubget", "text.txt")
        text = open(text_path, encoding="utf-8").read() if os.path.exists(text_path) else None
        if text is not None:
            text_lens.append(len(text))
            hash_ok += hashlib.sha256(text.encode()).hexdigest() == meta.get("source_text_hash")
        mpath = os.path.join(cdir, "processed", "pubget", "metadata.json")
        if os.path.exists(mpath) and json.load(open(mpath)).get("authors"):
            meta_authors += 1
        ipath = os.path.join(cdir, "identifiers.json")
        if os.path.exists(ipath):
            for k, v in json.load(open(ipath)).items():
                if v:
                    ids_present[k] += 1

        for a in rec.get("assessments") or []:
            at = (a.get("assessment_type") or {}).get("value")
            assess_type[at] += 1
            if at and ("task" in at.lower() or "behavio" in at.lower()):
                behav_assess.append((sid, (a.get("name") or {}).get("value"), at))
        tasks = rec.get("tasks") or []
        n_tasks_per.append(len(tasks))
        if not tasks:
            no_task_ids.append(sid)

        # Analyses -> tasks, and contrast cells that point at task conditions.
        cond_ids = {c["local_id"] for t in tasks for c in t.get("conditions") or []}
        level_conds = {}
        for me in rec.get("model_estimations") or []:
            for term in me.get("terms") or []:
                for lv in term.get("levels") or []:
                    level_conds[(term["local_id"], (lv.get("level") or {}).get("value"))] = \
                        set(lv.get("conditions") or [])
        used_tasks = set()
        for a in rec.get("analyses") or []:
            analyses_total += 1
            if a.get("tasks"):
                analyses_with_task += 1
                used_tasks |= set(a["tasks"])
            cells = (a.get("effect") or {}).get("cells") or []
            if any(level_conds.get((c.get("term"), (c.get("level") or {}).get("value")), set())
                   & cond_ids for c in cells):
                analyses_with_cond_cell += 1
        tasks_total += len(tasks)
        tasks_linked += sum(t["local_id"] in used_tasks for t in tasks)

        for t in tasks:
            nm = (t.get("name") or {}).get("value")
            if nm:
                key = nm.strip()
                name_counter[key] += 1
                norm_counter[norm_name(key)] += 1
                name_papers[key].add(sid)
            for fld in TASK_FIELDS:
                v = t.get(fld) or {}
                c = field_fill[fld]
                c["extracted" if filled(v) else (v.get("unreported_reason") or "not_reported")] += 1
                if filled(v):
                    c["src_" + (v.get("value_source") or "?")] += 1
                    c["evidence_" + ((v.get("evidence") or {}).get("status") or "?")] += 1
                    span_sets_per_field[len((v.get("evidence") or {}).get("sets") or [])] += 1
            for fld in TASK_FIELDS:
                v = t.get(fld) or {}
                if filled(v):
                    # pubget text pads punctuation with spaces ("Xia et al. ( 2020 )"),
                    # so compare with all whitespace removed.
                    sp = squash(" ".join(x["text"] for x in spans_of(v)))
                    for x in values(v):
                        if isinstance(x, str):
                            verbatim[fld]["in_span" if squash(x) in sp else "not_in_span"] += 1
            for fld in enum_vals:
                for x in values(t.get(fld)):
                    enum_vals[fld][x] += 1
            if filled(t.get("references")):
                for r in values(t["references"]):
                    ref_style["numeric" if NUMERIC_CITE.match(r.strip()) else "author_year/other"] += 1
                    if len(ref_examples) < 25:
                        ref_examples.append((nm, r))
            # Name appears verbatim in one of its evidence spans (span-level NER signal).
            if nm:
                sp = spans_of(t.get("name"))
                name_in_span["in_span" if any(squash(nm) in squash(s["text"]) for s in sp)
                             else ("no_span" if not sp else "not_verbatim")] += 1
            conds = t.get("conditions") or []
            n_conditions.append(len(conds))
            for cnd in conds:
                for fld in COND_FIELDS:
                    v = cnd.get(fld) or {}
                    cond_fill[fld]["extracted" if filled(v) else "not_reported"] += 1
                for x in values(cnd.get("condition_kind")):
                    cond_kind[x] += 1

            # Every span under this task, checked against the raw text.
            def walk(o):
                nonlocal span_total, span_exact
                if isinstance(o, dict):
                    if {"text", "start_char", "end_char"} <= set(o):
                        span_total += 1
                        span_lens.append(o["end_char"] - o["start_char"])
                        if text is not None and text[o["start_char"]:o["end_char"]] == o["text"]:
                            span_exact += 1
                        span_sections[section_class(sections, o["start_char"])] += 1
                        return
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(t)

    # Task-mentioning validator findings.
    val_task = collections.Counter()
    vpath = os.path.join(R, "final-validation.json")
    if os.path.exists(vpath):
        reps = json.load(open(vpath))["validation"]["reports"]
        for r in reps.values():
            for kind in ("errors", "warnings"):
                val_task[kind] += sum(".tasks[" in w for w in r.get(kind) or [])

    out.update({
        "extractor_model": dict(models), "extractor_version": dict(versions),
        "records_repaired": repaired,
        "source_hash_matches_text_txt": hash_ok,
        "text_chars_median": statistics.median(text_lens) if text_lens else None,
        "records_with_authors_in_metadata": meta_authors,
        "identifiers_present": dict(ids_present),
        "records_with_tasks": sum(n > 0 for n in n_tasks_per),
        "records_without_tasks": no_task_ids,
        "tasks_total": tasks_total,
        "tasks_per_record": dict(sorted(collections.Counter(n_tasks_per).items())),
        "unique_task_names": len(name_counter),
        "top_task_names": [(n, c, len(name_papers[n])) for n, c in
                           name_counter.most_common(args.top)],
        "normalized_task_names": norm_counter.most_common(),
        "assessments_total": sum(assess_type.values()),
        "assessment_types_top": assess_type.most_common(20),
        "behavioral_task_assessments": behav_assess,
        "task_field_fill": {k: dict(v) for k, v in field_fill.items()},
        "enum_values": {k: dict(v.most_common()) for k, v in enum_vals.items()},
        "conditions_total": sum(n_conditions),
        "conditions_per_task": dict(sorted(collections.Counter(n_conditions).items())),
        "condition_field_fill": {k: dict(v) for k, v in cond_fill.items()},
        "condition_kind": dict(cond_kind.most_common()),
        "reference_style": dict(ref_style), "reference_examples": ref_examples,
        "task_spans_total": span_total, "task_spans_exact_match": span_exact,
        "task_span_chars_median": statistics.median(span_lens) if span_lens else None,
        "task_span_sections": dict(span_sections.most_common()),
        "evidence_sets_per_filled_field": dict(sorted(span_sets_per_field.items())),
        "task_name_in_own_span": dict(name_in_span),
        "value_verbatim_in_spans": {k: dict(v) for k, v in verbatim.items()},
        "analyses_total": analyses_total, "analyses_with_task": analyses_with_task,
        "analyses_with_condition_cells": analyses_with_cond_cell,
        "tasks_referenced_by_an_analysis": tasks_linked,
        "validator_findings_on_tasks": dict(val_task),
    })

    for k, v in out.items():
        if k == "top_task_names":
            print(f"\n{k}: (name, occurrences, papers)")
            for n, c, p in v:
                print(f"  {c:3d} {p:3d}  {n}")
        elif isinstance(v, dict) and any(isinstance(x, dict) for x in v.values()):
            print(f"\n{k}:")
            for kk, vv in v.items():
                print(f"  {kk}: {vv}")
        else:
            print(f"{k}: {v}")
    if args.json:
        json.dump(out, open(args.json, "w"), indent=1)


if __name__ == "__main__":
    main()
