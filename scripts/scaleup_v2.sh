cd /home/james/taskcat
CONC=24 .venv/bin/python scripts/nuextract_infer_2pass.py data/passages_psych.jsonl nu-task-v2 8330 data/nux/v2_psych > logs/v2_psych.log 2>&1
echo psych-done $(date) >> logs/scaleup.log
CONC=24 .venv/bin/python scripts/nuextract_infer_2pass.py data/passages_train_rest.jsonl nu-task-v2 8330 data/nux/v2_train_rest > logs/v2_train_rest.log 2>&1
echo rest-done $(date) >> logs/scaleup.log
