#!/usr/bin/env bash
# [B300-004] One-shot Marshall 8x NVIDIA B300 Training, Eval & GGUF Export Runner
set -euo pipefail

echo "=== [1/5] Installing Python dependencies ==="
pip install -U -r requirements.txt

echo "=== [2/5] Validating dataset ==="
python3 scripts/validate_dataset.py --data-dir data

echo "=== [3/5] Ensuring llama.cpp is available ==="
LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-/opt/llama.cpp}"
if [ ! -d "$LLAMA_CPP_DIR" ]; then
    git clone --depth 1 https://github.com/ggerganov/llama.cpp "$LLAMA_CPP_DIR"
    cmake -B "$LLAMA_CPP_DIR/build" -S "$LLAMA_CPP_DIR"
    cmake --build "$LLAMA_CPP_DIR/build" --config Release -j"$(nproc)" --target llama-quantize
fi

echo "=== [4/5] Launching 8x B300 BF16 LoRA Fine-Tuning ==="
accelerate launch --num_processes=8 --mixed_precision=bf16 scripts/train_b300.py

echo "=== [5/5] Evaluating, Merging & Exporting GGUF (Q4_K_M, Q8_0) ==="
python3 scripts/eval_and_export.py --llama-cpp-dir "$LLAMA_CPP_DIR"

echo ""
echo "=================================================================="
echo "DONE! Copy artifacts off the node BEFORE releasing it:"
echo "  scp -r <user>@<b300-host>:$(pwd)/outputs/gguf ./outputs/"
echo "  scp -r <user>@<b300-host>:$(pwd)/outputs/merged-safetensors ./outputs/"
echo "=================================================================="
