#!/bin/bash
# merge v1 checkpoint (CPU, bf16) then serve with vLLM on 4 GPUs (TP2 x DP2) as nu-task-v3 on port 8330
set -u
cd /home/james/taskcat/ft
/home/james/venv-train/bin/python merge_task.py /home/james/taskcat/ft/ckpt-task-v3/final /home/james/taskcat/ft/merged-task-v3 > merge_v3.log 2>&1 || { echo merge failed >> merge_v3.log; exit 1; }
cd /tmp && VLLM_DISABLE_COMPILE_CACHE=1 PATH=/home/james/vllm-venv/bin:$PATH /home/james/vllm-venv/bin/vllm serve /home/james/taskcat/ft/merged-task-v3 \
  --served-model-name nu-task-v3 --host 127.0.0.1 --port 8330 --max-model-len 12288 --max-num-seqs 16 \
  --gpu-memory-utilization 0.92 --tensor-parallel-size 2 --data-parallel-size 2 --language-model-only --no-enable-prefix-caching \
  > /home/james/taskcat/ft/serve_v3.log 2>&1
