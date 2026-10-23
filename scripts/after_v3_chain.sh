#!/bin/bash
# wait for v3 training, merge + serve, evaluate on neuro gold (astra ref) and psych eval30 (Luna ref)
cd /home/james/taskcat
until grep -q "exited with" ft/train_task_v3.log; do sleep 30; done
cd ft && (./after_train_v3.sh &) ; cd ..
until grep -q "Application startup complete" ft/serve_v3.log 2>/dev/null; do sleep 15; grep -q failed ft/merge_v3.log 2>/dev/null && exit 1; done
CONC=24 .venv/bin/python scripts/nuextract_infer_2pass.py data/passages_gold.jsonl nu-task-v3 8330 data/nux/v3_gold
CONC=24 .venv/bin/python scripts/nuextract_infer_2pass.py data/passages_psych_eval30.jsonl nu-task-v3 8330 data/nux/v3_psych_eval30
{ echo "== neuro gold vs astra"; .venv/bin/python scripts/eval_dirs.py data/passages_gold.jsonl data/silver/gold_astra data/nux/v3_gold data/nux/v2_gold data/nux/v1_gold
  echo "== psych eval30 vs luna"; .venv/bin/python scripts/eval_dirs.py data/passages_psych_eval30.jsonl data/silver/psych_luna_eval data/nux/v3_psych_eval30 data/nux/v2_psych_eval30; } > logs/v3_eval.txt 2>&1
echo done >> logs/v3_eval.txt
