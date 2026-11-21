---
license: apache-2.0
base_model: Qwen/Qwen3.8-27B
tags:
  - reverse-engineering
  - decompilation
  - ghidra
  - ida-pro
  - binary-analysis
  - gguf
  - qwen3.8
  - cybersecurity
  - local-llm
language:
  - en
---

# ReverseEng-Qwen3.8-27B-GGUF

**Offline 27B Binary Reverse Engineering & Decompilation Specialist (262K Context)** — fine-tuned on `8x NVIDIA B300` GPUs from `Qwen/Qwen3.8-27B` for `x86_64` & `ARM64` assembly-to-C/Rust decompilation, Ghidra/IDA Pro pseudocode cleanup, struct/type recovery, and static vulnerability/anti-debug analysis.

Runs **100% locally** on a single 24GB GPU (RTX 3090/4090) or 24GB+ Apple Silicon Mac (`Q4_K_M`, ~16.7 GB) with zero cloud API leakage.

## Quickstart (Ollama)

```bash
huggingface-cli download backerv/ReverseEng-Qwen3.8-27B-GGUF reverseeng-qwen3.8-27b-Q4_K_M.gguf Modelfile.reverseeng --local-dir .
ollama create reverseeng-27b -f Modelfile.reverseeng
ollama run reverseeng-27b
```

## Quickstart (`llama.cpp`)

```bash
./llama-server -m reverseeng-qwen3.8-27b-Q4_K_M.gguf -c 32768 -ngl 99 --port 8080
```

---

## Commercial Pro Model Suite (8x B300 Fine-Tuned `Qwen3.8-27B` Collection)

`ReverseEng-Qwen3.8-27B-GGUF` is the free public release from our **27B Air-Gapped Specialist Suite**. Need private, whole-repo auditing, offensive/defensive AppSec, or algorithmic trading models with full LoRA adapters and CLI tooling?

| Model | Domain & Capabilities | Training Corpus | Price (USDC on Solana) |
| :--- | :--- | :--- | :--- |
| **ReverseEng-Qwen3.8-27B** | `x86_64`/`ARM64` decompilation, Ghidra/IDA cleanup, ELF/PE static analysis | `1,200` train / `150` eval | **FREE (Public)** |
| **SolSec-Qwen3.8-27B** | Smart-contract security auditor (`Solidity` + `Solana Rust/Anchor`), PoC exploits, patches + `solsec_cli.py` | `1,062` train / `117` eval (Slither-audited + Anchor) | **$49 USDC** |
| **AppSec-Qwen3.8-27B** | Multi-language SAST & defensive patching (`Python`, `TS/JS`, `Go`, `Rust`, `C++`, `Java`, `SQL`) | `1,200` train / `150` eval | **$49 USDC** |
| **AlphaQuant-Qwen3.8-27B** | Quant strategies (`Freqtrade`, `PineScript`, `vectorbt`), risk engines, backtest sanity | `1,200` train / `150` eval | **$49 USDC** |
| **Full Security & Quant Bundle** | **All 4 Pro Models** (`Q4_K_M` GGUFs + `LoRA` adapters + `solsec_cli.py` + `Modelfiles`) | Full Suite | **$119 USDC** |

### Verified Benchmark Highlight (`SolSec-Qwen3.8-27B` vs. Base `Qwen3.8-27B`, 25-sample held-out eval)
| Metric | Base `Qwen3.8-27B` | Fine-Tuned `SolSec-Qwen3.8-27B` |
| :--- | :---: | :---: |
| Structured JSON Validity | `36.0%` | **`100.0%`** |
| Severity Classification Accuracy | `0.0%` | **`100.0%`** |
| False-Positive Rejection Rate | `88.9%` | **`100.0%`** |

### Instant Automated Purchase (24/7 Serverless Telegram Bot — Zero-KYC Solana USDC)
Order and receive instant download links automatically via **[@backerv_bot](https://t.me/backerv_bot)** (`https://t.me/backerv_bot`) using **Solana USDC** — zero KYC, zero platform fees.
