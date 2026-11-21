---
license: apache-2.0
base_model: Qwen/Qwen3.8-27B
tags:
  - appsec
  - sast
  - security
  - code-audit
  - gguf
---

# AppSec-Qwen3.8-27B

Local, air-gapped multi-language SAST Auditor & Remediation Engineer (Python, TS/JS, Go, Rust, C++, Java, PHP, SQL) fine-tuned on `Qwen/Qwen3.8-27B`.

## Benchmarks (Base vs. Fine-Tuned)

| Metric | Base (`Qwen3.8-27B`) | Fine-Tuned (`AppSec-27B`) |
| :--- | :---: | :---: |
| JSON Schema Validity | `{{BASE_JSON}}` | `{{FT_JSON}}` |
| Severity Accuracy | `{{BASE_SEV}}` | `{{FT_SEV}}` |
| False-Positive Rejection | `{{BASE_FP}}` | `{{FT_FP}}` |

## Quickstart (Ollama)

```bash
ollama create appsec-qwen3.8-27b -f Modelfile.appsec
python solsec_cli.py --mode appsec --target ./src --fail-on-high
```
