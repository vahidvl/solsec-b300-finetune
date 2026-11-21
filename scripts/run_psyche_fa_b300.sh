#!/usr/bin/env bash
# [B300-PSYCHE-001] Turnkey 8x B300 Runner for PsycheFa-Qwen3.8-27B
set -euo pipefail

NUM_GPUS=$(nvidia-smi -L | wc -l)
LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$HOME/llama.cpp}"
echo "Detected ${NUM_GPUS} GPUs | Using llama.cpp at ${LLAMA_CPP_DIR}"

echo "=== [1/3] Validating PsycheFa dataset ==="
python3 scripts/build_psyche_fa_dataset.py --validate-only --data-dir data

echo "=== [2/3] Launching ${NUM_GPUS}x B300 BF16 LoRA Fine-Tuning (PsycheFa) ==="
accelerate launch --num_processes="$NUM_GPUS" --mixed_precision=bf16 scripts/train_b300.py \
    --train-file data/psyche_fa_train.jsonl \
    --eval-file data/psyche_fa_eval.jsonl \
    --output-dir outputs/lora-psyche-fa

echo "=== [3/3] Exporting GGUF (Q4_K_M, Q8_0) & Fast Eval ==="
python3 scripts/eval_and_export.py \
    --lora-dir outputs/lora-psyche-fa \
    --eval-file data/psyche_fa_eval.jsonl \
    --merged-dir outputs/merged-psyche-fa \
    --gguf-dir outputs/gguf \
    --llama-cpp-dir "$LLAMA_CPP_DIR" \
    --model-prefix psyche-fa-qwen3.8-27b \
    --skip-base-eval \
    --eval-limit 1
rm -rf outputs/merged-psyche-fa
echo "Removed intermediate outputs/merged-psyche-fa to save disk."

echo ""
echo "=================================================================="
echo "DONE! Copy PsycheFa GGUF artifacts off the B300 node:"
echo "  scp <user>@<b300-host>:$(pwd)/outputs/gguf/psyche-fa-qwen3.8-27b-Q4_K_M.gguf ./outputs/gguf/"
echo "  scp <user>@<b300-host>:$(pwd)/outputs/gguf/psyche-fa-qwen3.8-27b-Q8_0.gguf ./outputs/gguf/"
echo "  scp <user>@<b300-host>:$(pwd)/outputs/gguf/psyche-fa-qwen3.8-27b_eval_report.json ./outputs/gguf/"
echo "=================================================================="
