---
license: apache-2.0
base_model: Qwen/Qwen3.8-27B
tags:
  - quantitative-finance
  - algorithmic-trading
  - freqtrade
  - pinescript
  - gguf
---

# AlphaQuant-Qwen3.8-27B

Local Quantitative Finance & Algorithmic Trading Engineer (Freqtrade `IStrategy`, PineScript v5/v6, `vectorbt`, VaR/CVaR & Kelly risk engines) fine-tuned on `Qwen/Qwen3.8-27B`.

## Benchmarks (Base vs. Fine-Tuned)

| Metric | Base (`Qwen3.8-27B`) | Fine-Tuned (`AlphaQuant-27B`) |
| :--- | :---: | :---: |
| JSON Schema Validity | `{{BASE_JSON}}` | `{{FT_JSON}}` |
| Severity Accuracy | `{{BASE_SEV}}` | `{{FT_SEV}}` |
| False-Positive Rejection | `{{BASE_FP}}` | `{{FT_FP}}` |

## Quickstart (Ollama)

```bash
ollama create alphaquant-qwen3.8-27b -f Modelfile.alphaquant
python solsec_cli.py --mode alphaquant --prompt "Build a 15m EMA+RSI Freqtrade IStrategy with ATR trailing stop"
```
