#!/bin/bash
# taskcat v3: continue v2 for 1 epoch on Luna neuro + psych silver (psych x2), lr 5e-5 decay
# (LoRA attn 32 / MLP 12 / mixers 16, in_proj_a/b 4; A_log, dt_bias, conv1d, norms direct; fp32 masters).
set -u
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /home/james/taskcat/ft
/home/james/venv-train/bin/torchrun --nproc_per_node=4 train_task.py \
  --data /home/james/taskcat/data/ft/train_v3.jsonl --out /home/james/taskcat/ft/ckpt-task-v3 \
  --epochs ${EPOCHS:-1} --lr 5e-5 --init-from /home/james/taskcat/ft/ckpt-task-v2/final --sched decay --slow-lr-div 1 --max-tokens 6000 --dropout 0.1 \
  --save-every 40 --log-every 5 --run-name task-v3 --no-trackio > /home/james/taskcat/ft/train_task_v3.log 2>&1
echo "exited with $?" >> /home/james/taskcat/ft/train_task_v3.log
