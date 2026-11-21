# Marshall `8× NVIDIA B300` Execution Guide

> **Zero Idle GPU Burn:** All scripts and datasets are pre-validated locally (`0` schema errors). Follow these exact copy-paste steps so the `8× B300` node (`$0.53/min`) is used strictly for training, eval, and GGUF export.

---

## 1. Request the `8× NVIDIA B300` Node (Marshall Web Console)

1. Open the Marshall Web Console.
2. Submit a `public_research_request` for **8× NVIDIA B300 (288 GB)**.
3. Once provisioned, copy your SSH connection string (e.g., `ssh -i ~/.ssh/marshall_key user@<b300-host>`).

---

## 2. Upload Project & Dataset to the Node

Run from your local machine inside `F:\Develop\NationalCompute-Monetization\02-B300-Finetune-Asset`:

```bash
scp -r SPEC.md requirements.txt scripts data <user>@<b300-host>:~/b300-auditor/
```

---

## 3. Run Turnkey Training, Eval & GGUF Export (On Node)

SSH into the node and execute the one-shot runner:

```bash
ssh <user>@<b300-host>
cd ~/b300-auditor
bash scripts/run_on_b300.sh
```

`run_on_b300.sh` automatically:
1. Installs `requirements.txt`.
2. Re-validates `data/train.jsonl` and `data/eval_benchmark.jsonl`.
3. Clones & builds `llama.cpp` (`llama-quantize`) if not present.
4. Launches `accelerate launch --num_processes=8 --mixed_precision=bf16 scripts/train_b300.py`.
5. Runs `scripts/eval_and_export.py` (evaluates base vs fine-tuned, merges LoRA to `safetensors`, exports `Q4_K_M` & `Q8_0` GGUFs).

---

## 4. Copy Artifacts Off Node & Release Immediately

**CRITICAL:** Node NVMe is wiped on release. Run these `scp` commands from your local machine **before** clicking Release in Marshall:

```bash
scp -r <user>@<b300-host>:~/b300-auditor/outputs/gguf ./outputs/
scp -r <user>@<b300-host>:~/b300-auditor/outputs/merged-safetensors ./outputs/
```

Then immediately **Release** the `8× B300` node in the Marshall Web Console.
