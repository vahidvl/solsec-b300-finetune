#!/usr/bin/env bash
# [B300-REVENG-001] Turnkey 8x B300 Runner for ReverseEng-Qwen3.8-27B
set -euo pipefail

NUM_GPUS=$(nvidia-smi -L | wc -l)
LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$HOME/llama.cpp}"
echo "Detected ${NUM_GPUS} GPUs | Using llama.cpp at ${LLAMA_CPP_DIR}"

echo "=== [1/4] Validating ReverseEng dataset ==="
python3 scripts/build_reverseeng_dataset.py --validate-only --data-dir data

echo "=== [2/4] Launching ${NUM_GPUS}x B300 BF16 LoRA Fine-Tuning (ReverseEng) ==="
accelerate launch --num_processes="$NUM_GPUS" --mixed_precision=bf16 scripts/train_b300.py \
    --train-file data/reverseeng_train.jsonl \
    --eval-file data/reverseeng_eval.jsonl \
    --output-dir outputs/lora-reverseeng

echo "=== [3/4] Exporting GGUF (Q4_K_M) & Fast Eval ==="
python3 scripts/eval_and_export.py \
    --lora-dir outputs/lora-reverseeng \
    --eval-file data/reverseeng_eval.jsonl \
    --merged-dir outputs/merged-reverseeng \
    --gguf-dir outputs/gguf \
    --llama-cpp-dir "$LLAMA_CPP_DIR" \
    --model-prefix reverseeng-qwen3.8-27b \
    --skip-base-eval \
    --eval-limit 1

rm -rf outputs/merged-reverseeng
rm -f outputs/gguf/reverseeng-qwen3.8-27b-Q8_0.gguf
echo "Cleaned up outputs/merged-reverseeng and Q8_0 GGUF."

if [ -n "${HF_TOKEN:-}" ]; then
    echo "=== [4/4] Uploading ReverseEng-Qwen3.8-27B-GGUF to Hugging Face ==="
    python3 - <<'PY'
import os
from huggingface_hub import HfApi

api = HfApi(token=os.environ["HF_TOKEN"])
username = api.whoami()["name"]
repo_id = f"{username}/ReverseEng-Qwen3.8-27B-GGUF"
api.create_repo(repo_id=repo_id, repo_type="model", private=True, exist_ok=True)
for local, remote in [
    ("outputs/gguf/reverseeng-qwen3.8-27b-Q4_K_M.gguf", "reverseeng-qwen3.8-27b-Q4_K_M.gguf"),
    ("outputs/gguf/reverseeng-qwen3.8-27b_eval_report.json", "reverseeng-qwen3.8-27b_eval_report.json"),
    ("release-kit/Modelfile.reverseeng", "Modelfile.reverseeng"),
    ("release-kit/HF_MODEL_CARD_REVERSEENG.md", "README.md"),
]:
    if os.path.exists(local):
        api.upload_file(path_or_fileobj=local, path_in_repo=remote, repo_id=repo_id, repo_type="model")
if os.path.isdir("outputs/lora-reverseeng"):
    api.upload_folder(
        folder_path="outputs/lora-reverseeng",
        path_in_repo="lora-adapter",
        repo_id=repo_id,
        repo_type="model",
        ignore_patterns=["checkpoint-*", "**/checkpoint-*"],
    )
print(f"[PASS] Uploaded {repo_id}")
PY
fi
