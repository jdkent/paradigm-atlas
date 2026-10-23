#!/bin/bash
# taskcat v1: NuExtract3 fine-tune on Luna silver TaskMention labels (template v0.2), same config as prose-n5v3
# (LoRA attn 32 / MLP 12 / mixers 16, in_proj_a/b 4; A_log, dt_bias, conv1d, norms direct; fp32 masters).
set -u
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /home/james/taskcat/ft
/home/james/venv-train/bin/torchrun --nproc_per_node=4 train_task.py \
  --data /home/james/taskcat/data/ft/train_luna_v1.jsonl --out /home/james/taskcat/ft/ckpt-task-v1 \
  --epochs ${EPOCHS:-3} --lr 1e-4 --slow-lr-div 1 --max-tokens 6000 --dropout 0.1 \
  --save-every 40 --log-every 5 --run-name task-v1 --no-trackio > /home/james/taskcat/ft/train_task_v1.log 2>&1
echo "exited with $?" >> /home/james/taskcat/ft/train_task_v1.log
