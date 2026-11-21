#!/usr/bin/env bash
# [B300-EXTRA-001] Sequential 8x B300 Runner for Model #2 (AppSec) & Model #3 (AlphaQuant)
set -euo pipefail

NUM_GPUS=$(nvidia-smi -L | wc -l)
LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$HOME/llama.cpp}"
echo "Detected ${NUM_GPUS} GPUs | Using llama.cpp at ${LLAMA_CPP_DIR}"

echo "=== [1/5] Validating AppSec & AlphaQuant datasets ==="
python3 scripts/build_extra_datasets.py --validate-only --data-dir data

echo "=== [2/5] Training Model #2: appsec-qwen3.8-27b ==="
accelerate launch --num_processes="$NUM_GPUS" --mixed_precision=bf16 scripts/train_b300.py \
    --train-file data/appsec_train.jsonl \
    --eval-file data/appsec_eval.jsonl \
    --output-dir outputs/lora-appsec

echo "=== [3/5] Exporting & Evaluating Model #2: appsec-qwen3.8-27b ==="
python3 scripts/eval_and_export.py \
    --lora-dir outputs/lora-appsec \
    --eval-file data/appsec_eval.jsonl \
    --merged-dir outputs/merged-appsec \
    --gguf-dir outputs/gguf \
    --llama-cpp-dir "$LLAMA_CPP_DIR" \
    --model-prefix appsec-qwen3.8-27b \
    --eval-limit 25
rm -rf outputs/merged-appsec
echo "Removed intermediate outputs/merged-appsec to save disk."

echo "=== [4/5] Training Model #3: alphaquant-qwen3.8-27b ==="
accelerate launch --num_processes="$NUM_GPUS" --mixed_precision=bf16 scripts/train_b300.py \
    --train-file data/alphaquant_train.jsonl \
    --eval-file data/alphaquant_eval.jsonl \
    --output-dir outputs/lora-alphaquant

echo "=== [5/5] Exporting & Evaluating Model #3: alphaquant-qwen3.8-27b ==="
python3 scripts/eval_and_export.py \
    --lora-dir outputs/lora-alphaquant \
    --eval-file data/alphaquant_eval.jsonl \
    --merged-dir outputs/merged-alphaquant \
    --gguf-dir outputs/gguf \
    --llama-cpp-dir "$LLAMA_CPP_DIR" \
    --model-prefix alphaquant-qwen3.8-27b \
    --eval-limit 25
rm -rf outputs/merged-alphaquant
echo "Removed intermediate outputs/merged-alphaquant to save disk."

echo ""
echo "=================================================================="
echo "DONE! Copy all GGUF artifacts & eval reports off the B300 node:"
echo "  scp <user>@<b300-host>:$(pwd)/outputs/gguf/appsec-qwen3.8-27b-Q4_K_M.gguf ./outputs/gguf/"
echo "  scp <user>@<b300-host>:$(pwd)/outputs/gguf/appsec-qwen3.8-27b-Q8_0.gguf ./outputs/gguf/"
echo "  scp <user>@<b300-host>:$(pwd)/outputs/gguf/appsec-qwen3.8-27b_eval_report.json ./outputs/gguf/"
echo "  scp <user>@<b300-host>:$(pwd)/outputs/gguf/alphaquant-qwen3.8-27b-Q4_K_M.gguf ./outputs/gguf/"
echo "  scp <user>@<b300-host>:$(pwd)/outputs/gguf/alphaquant-qwen3.8-27b-Q8_0.gguf ./outputs/gguf/"
echo "  scp <user>@<b300-host>:$(pwd)/outputs/gguf/alphaquant-qwen3.8-27b_eval_report.json ./outputs/gguf/"
echo "=================================================================="
