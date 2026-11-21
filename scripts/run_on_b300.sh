#!/usr/bin/env bash
# [B300-004 / B300-HARDEN-001] One-shot Marshall 8x NVIDIA B300 Runner
set -euo pipefail

echo "=== [1/6] Checking GPU availability ==="
python3 -c "import torch; assert torch.cuda.is_available(), 'CUDA not available!'"
NUM_GPUS=$(nvidia-smi -L | wc -l)
echo "Detected $NUM_GPUS GPUs"

echo "=== [2/6] Installing Python dependencies (preserving CUDA PyTorch) ==="
pip install -U -r requirements.txt
if ! python3 -c "from transformers.models import qwen3_5" 2>/dev/null; then
    echo "Installing latest transformers from GitHub for Qwen3.8/3.5 support..."
    pip install -U git+https://github.com/huggingface/transformers.git
fi

echo "=== [3/6] Validating dataset ==="
python3 scripts/validate_dataset.py --data-dir data

echo "=== [4/6] Ensuring ggml-org/llama.cpp is available ==="
LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$HOME/llama.cpp}"
if [ ! -d "$LLAMA_CPP_DIR" ]; then
    git clone --depth 1 https://github.com/ggml-org/llama.cpp "$LLAMA_CPP_DIR"
    cmake -B "$LLAMA_CPP_DIR/build" -S "$LLAMA_CPP_DIR" -DGGML_CUDA=OFF
    cmake --build "$LLAMA_CPP_DIR/build" --config Release -j"$(nproc)" --target llama-quantize
fi
pip install -e "$LLAMA_CPP_DIR/gguf-py"

echo "=== [5/6] Launching ${NUM_GPUS}x B300 BF16 LoRA Fine-Tuning ==="
accelerate launch --num_processes="$NUM_GPUS" --mixed_precision=bf16 scripts/train_b300.py

echo "=== [6/6] Exporting GGUF (Q4_K_M, Q8_0) & Running Fast Eval ==="
python3 scripts/eval_and_export.py --llama-cpp-dir "$LLAMA_CPP_DIR" --eval-limit 25

echo ""
echo "=================================================================="
echo "DONE! Copy artifacts off the node BEFORE releasing it:"
echo "  scp -r <user>@<b300-host>:$(pwd)/outputs/gguf ./outputs/"
echo "  scp -r <user>@<b300-host>:$(pwd)/outputs/merged-safetensors ./outputs/"
echo "=================================================================="
