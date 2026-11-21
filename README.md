# Air-Gapped 27B Specialist LLM Suite (`Qwen3.8-27B` Fine-Tunes)

Production fine-tuning pipeline, whole-repo CLI scanner (`release-kit/solsec_cli.py`), and commercial **GGUF (`Q4_K_M`, 262K context)** model suite trained on `8x NVIDIA B300 (288GB)` GPUs.

## Free Public Model
- **[backerv/ReverseEng-Qwen3.8-27B-GGUF](https://huggingface.co/backerv/ReverseEng-Qwen3.8-27B-GGUF)** — Offline `x86_64`/`ARM64` assembly-to-C/Rust decompilation, Ghidra/IDA pseudocode cleanup, and ELF/PE static analysis (`1,200` train / `150` eval).

## Commercial Pro Models (`GGUF` + `LoRA` Adapters + `solsec_cli.py`)
| Model | Specialization | Verified Eval | Price |
| :--- | :--- | :--- | :--- |
| **SolSec-Qwen3.8-27B** | Smart-Contract Security (`Solidity` + `Solana Rust/Anchor`), PoC & Patch | `100%` JSON / `100%` Severity / `100%` FP Rejection (vs Base `36%`/`0%`/`88.9%` on 25 held-out cases) | **$49 USDC** |
| **AppSec-Qwen3.8-27B** | Multi-Language SAST (`Python`, `TS/JS`, `Go`, `Rust`, `C++`, `SQL`) | `1,200` train / `150` eval | **$49 USDC** |
| **AlphaQuant-Qwen3.8-27B** | Quant & Algo Trading (`Freqtrade`, `PineScript`, `vectorbt`, Risk Engines) | `1,200` train / `150` eval | **$49 USDC** |
| **Full Pro Bundle** | All Pro GGUFs + LoRA adapters + `release-kit/solsec_cli.py` | Full Suite | **$119 USDC** |

## Whole-Repo CLI Scanner Quickstart
```bash
# Scan an entire Solana/Solidity project locally via Ollama or llama-server
python3 release-kit/solsec_cli.py --mode solsec --target ./contracts --out audit_report.md --fail-on-high

# Scan a web/backend repo (Python/TS/Go/Rust/SQL)
python3 release-kit/solsec_cli.py --mode appsec --target ./src --out appsec_report.md
```

## License
Pipeline & CLI tooling are open-source; trained commercial Pro weights are licensed per purchase.
