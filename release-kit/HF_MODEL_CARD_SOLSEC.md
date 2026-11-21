---
license: apache-2.0
base_model: Qwen/Qwen3.8-27B
tags:
  - security
  - smart-contracts
  - solana
  - solidity
  - gguf
---

# SolSec-Qwen3.8-27B

Local, air-gapped Web3 Smart-Contract Security Auditor (Solana/Anchor & EVM/Solidity) fine-tuned on `Qwen/Qwen3.8-27B`.

## Benchmarks (Base vs. Fine-Tuned)

| Metric | Base (`Qwen3.8-27B`) | Fine-Tuned (`SolSec-27B`) |
| :--- | :---: | :---: |
| JSON Schema Validity | `{{BASE_JSON}}` | `{{FT_JSON}}` |
| Severity Accuracy | `{{BASE_SEV}}` | `{{FT_SEV}}` |
| False-Positive Rejection | `{{BASE_FP}}` | `{{FT_FP}}` |

## Quickstart (Ollama)

```bash
ollama create solsec-qwen3.8-27b -f Modelfile.solsec
python solsec_cli.py --mode solsec --target ./contracts --fail-on-high
```
